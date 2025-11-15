"""
Funções de formatação de dados
"""
from datetime import datetime
from typing import Union

def format_area(area_m2: float, unit: str = 'auto') -> str:
    """
    Formata área para exibição
    
    Parameters:
    -----------
    area_m2 : float
        Área em metros quadrados
    unit : str
        Unidade: 'auto', 'ha', 'km2'
        
    Returns:
    --------
    str
        Área formatada
        
    Exemplo:
    --------
    format_area(50000000)  # → "50.00 km²"
    """
    if unit == 'auto':
        if area_m2 < 10000:  # < 1 ha
            return f"{area_m2:.2f} m²"
        elif area_m2 < 1000000:  # < 1 km²
            return f"{area_m2/10000:.2f} ha"
        else:
            return f"{area_m2/1000000:.2f} km²"
    
    elif unit == 'ha':
        return f"{area_m2/10000:.2f} ha"
    
    elif unit == 'km2':
        return f"{area_m2/1000000:.2f} km²"
    
    else:
        return f"{area_m2:.2f} m²"

def format_date(date: Union[str, datetime], format_str: str = '%d/%m/%Y') -> str:
    """
    Formata data para exibição
    
    Parameters:
    -----------
    date : str ou datetime
        Data a formatar
    format_str : str
        Formato desejado
        
    Returns:
    --------
    str
        Data formatada
        
    Exemplo:
    --------
    format_date('2025-11-14')  # → "14/11/2025"
    """
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except:
            return date
    
    return date.strftime(format_str)

def format_number(number: float, decimals: int = 2) -> str:
    """
    Formata número com separadores de milhar
    
    Parameters:
    -----------
    number : float
        Número a formatar
    decimals : int
        Casas decimais
        
    Returns:
    --------
    str
        Número formatado
        
    Exemplo:
    --------
    format_number(1234567.89)  # → "1.234.567,89"
    """
    # Formata com separadores (locale-aware)
    return f"{number:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
