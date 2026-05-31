import os
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QPoint, Signal

from ui.styles.theme import Theme
from ui.window.components.rw_rotatable_label import RotatableLabel
from core.accessory_manager import AccessoryManager

class RenderWindow(QWidget):
    """
    Janela de renderização principal (Overlay).
    Responsável por exibir o avatar, gerenciar acessórios e lidar com
    a interação do usuário (arrastar e posicionar).
    """
    effectPositionChanged = Signal(int, int)

    def __init__(self, config_manager):
        super().__init__(None) 
        self.cfg = config_manager
        self.movie_cache = {}
        self.current_state = None # Estado atual do GIF (ex: mute, low, high)
        
        # Configurações de Janela: Transparente, Sem Bordas e Sempre no Topo
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # AJUSTE: Aumentado para 2048 para remover o "limite" de movimento ao redor do avatar
        self.canvas_size = 2048 
        self.setFixedSize(self.canvas_size, self.canvas_size)
        
        # Label principal do Avatar
        self.main_label = RotatableLabel(self)
        self.main_label.setAlignment(Qt.AlignCenter)
        
        # Gerenciador de Acessórios (Camadas extras)
        self.accessories = AccessoryManager(self, config_manager)
        
        # Variáveis de controle de arrasto
        self._drag_target = None  # ID do acessório ou "window"
        self._drag_offset = QPoint()

        # Posicionamento inicial da janela
        r = self.cfg.data.get("render", {})
        self.move(r.get("x", 100), r.get("y", 100))
        self.update_geometry()

    def update_geometry(self):
        """
        Atualiza o tamanho e a posição do avatar e acessórios com base na escala.
        Calcula o centro do canvas para evitar deslocamentos indesejados.
        """
        scale = self.cfg.data["render"].get("scale", 1.0)
        avatar_size = int(Theme.BASE_AVATAR_SIZE * scale)
        
        # Centraliza o avatar no novo canvas de 2048x2048
        offset = (self.canvas_size - avatar_size) // 2
        self.main_label.setGeometry(offset, offset, avatar_size, avatar_size)
        
        # Atualiza a posição de todos os acessórios ativos
        self.accessories.update(self.main_label)
        
        # Sincroniza coordenadas globais da janela
        self.cfg.data["render"]["x"] = self.x()
        self.cfg.data["render"]["y"] = self.y()

    def set_animation(self, path, state=None):
        """
        Define o GIF atual do avatar.
        :param path: Caminho do arquivo .gif
        :param state: String identificadora do estado (mute, low, etc)
        """
        if state: self.current_state = state

        if not path or not os.path.exists(path):
            if self.main_label.movie(): self.main_label.movie().stop()
            self.main_label.setMovie(None)
            self.main_label.clear()
            return
        
        # Gerenciamento de Cache para evitar stuttering ao trocar de GIF
        if path not in self.movie_cache:
            m = QMovie(path)
            m.setCacheMode(QMovie.CacheAll)
            self.movie_cache[path] = m
        
        target_movie = self.movie_cache[path]
        
        if self.main_label.movie() != target_movie:
            self.main_label.setMovie(target_movie)
            target_movie.start()
            self.raise_()

    # --- Lógica de Interação e Movimento ---

    def mousePressEvent(self, event):
        """ Detecta em qual item o usuário clicou para iniciar o arrasto. """
        if event.button() != Qt.LeftButton: return
        
        # Posição do clique relativa à janela (canvas)
        pos = event.position().toPoint()
        
        # 1. Verifica se clicou em algum acessório (Prioridade para camadas de cima)
        for l_id, lbl in reversed(list(self.accessories.widgets.items())):
            if lbl.isVisible() and lbl.geometry().contains(pos):
                layer_cfg = self.cfg.data.get("aux_layers", {}).get(l_id, {})
                if not layer_cfg.get("locked", False): # Só move se não estiver travado
                    self._drag_target = l_id
                    self._drag_offset = pos - lbl.pos()
                    return
        
        # 2. Verifica se clicou no avatar principal para mover a janela toda
        if self.main_label.geometry().contains(pos):
            if not self.cfg.data["render"].get("locked", False):
                self._drag_target = "window"
                # Offset global para movimento suave da janela
                self._drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        """ Processa o movimento do item selecionado. """
        if not self._drag_target: return
        
        if self._drag_target == "window":
            # Movimentação da Janela Inteira
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)
            self.cfg.data["render"]["x"] = new_pos.x()
            self.cfg.data["render"]["y"] = new_pos.y()
        
        else:
            # Movimentação de Acessório Específico
            l_id = self._drag_target
            new_pos = event.position().toPoint() - self._drag_offset
            self.accessories.widgets[l_id].move(new_pos)
            
            # Atualiza os dados no arquivo de configuração
            if l_id in self.cfg.data["aux_layers"]:
                c = self.cfg.data["aux_layers"][l_id]
                
                # AJUSTE: Salva o CENTRO do acessório para evitar o deslocamento diagonal ao escalar
                # O centro é a posição atual (new_pos) + metade do tamanho do widget
                lbl_widget = self.accessories.widgets[l_id]
                center_x = new_pos.x() + (lbl_widget.width() // 2)
                center_y = new_pos.y() + (lbl_widget.height() // 2)
                
                c["x"] = center_x
                c["y"] = center_y
                
                # AJUSTE: Coordenadas Relativas baseadas na distância entre centros
                # Isso impede que o acessório "fuja" para a diagonal quando você muda a escala
                avatar_center_x = self.main_label.x() + (self.main_label.width() // 2)
                avatar_center_y = self.main_label.y() + (self.main_label.height() // 2)
                
                c["rel_x"] = center_x - avatar_center_x
                c["rel_y"] = center_y - avatar_center_y

    def mouseReleaseEvent(self, event):
        """ Finaliza o arrasto e salva as configurações no disco. """
        if self._drag_target:
            self.cfg.save()
        self._drag_target = None