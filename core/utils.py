# core/utils.py
import os

def validate_path(path):
    """Verifica se o arquivo existe e é válido."""
    return path and os.path.exists(path)

def get_extension(path):
    """Retorna a extensão do arquivo em minúsculas."""
    return path.lower().split('.')[-1] if path else ""

def calculate_scale(base_size, scale_factor):
    """Calcula o novo tamanho inteiro baseado em um fator de escala."""
    return int(base_size * max(0.1, scale_factor))

def map_relative_to_absolute(rel_x, rel_y, parent_x, parent_y):
    """Converte posição relativa ao avatar para posição absoluta na tela."""
    return parent_x + rel_x, parent_y + rel_y

def map_absolute_to_relative(abs_x, abs_y, parent_x, parent_y):
    """Converte posição absoluta na tela para posição relativa ao avatar."""
    return abs_x - parent_x, abs_y - parent_y