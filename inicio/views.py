from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
import sympy as sp
import numpy as np
import json
import math
def inicio(request):
    return render(request,'index.html')

def resolver(request):
    return render(request,'resolver.html')

def grafica_deriv(request):
    return render(request,'graficar_derivadas.html')

def login_regis(request):
    return render(request,'login.html')

def grafica_limit(request):
    context = {}
    if request.method == 'POST':
        funcion = request.POST.get('funcion', '').strip()
        c_text = request.POST.get('c', '').strip()  # opcional: campo para c
        # valor por defecto de c si no se envía
        if c_text == '':
            c_text = '0'

        # símbolo independiente
        x = sp.symbols('x')

        # whitelist de funciones y constantes que permitimos en sympify
        allowed = {
            'x': x,
            # constantes
            'pi': sp.pi, 'E': sp.E,
            # funciones comunes
            'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
            'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
            'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
            'exp': sp.exp, 'log': sp.log, 'sqrt': sp.sqrt,
            'Abs': sp.Abs,
            # para usuarios más avanzados puedes añadir más funciones
        }

        try:
            # parsear expr y c
            expr = sp.sympify(funcion, locals=allowed)
            c_sym = sp.sympify(c_text, locals=allowed)
        except Exception as e:
            context['error'] = f"Error al parsear la función o c: {e}"
            return render(request, 'graficar_limites.html', context)

        # Intentar calcular límite simbólico
        try:
            limite_sym = sp.limit(expr, x, c_sym)
            limite_str = sp.srepr(limite_sym)  # representación técnica
            # intentar obtener forma legible
            try:
                limite_pretty = sp.N(limite_sym)
            except Exception:
                limite_pretty = limite_sym
        except Exception as e:
            limite_sym = None
            limite_pretty = None
            context['limite_error'] = f"No se pudo calcular límite simbólico: {e}"

        # Generar rango para gráfica (usa entorno alrededor de c)
        try:
            c_val = float(sp.N(c_sym))
        except Exception:
            c_val = 0.0

        x_min = c_val - 5
        x_max = c_val + 5
        N = 600
        xs = np.linspace(x_min, x_max, N)

        # crear función numérica segura con lambdify (numpy/mpmath)
        try:
            f_num = sp.lambdify(x, expr, modules=['numpy', 'mpmath'])
        except Exception as e:
            context['error'] = f"No se pudo convertir la función a numérica: {e}"
            return render(request, 'graficar_limites.html', context)

        ys = []
        for xi in xs:
            try:
                yi = f_num(xi)
                # si devuelve mpmath mpf, convertir a float
                if hasattr(yi, 'real') and hasattr(yi, 'imag'):
                    # complejo -> lo manejamos convirtiendo a NaN si tiene parte imaginaria
                    if abs(yi.imag) > 1e-12:
                        yi = float('nan')
                    else:
                        yi = float(yi.real)
                else:
                    yi = float(yi)
                # NaN o inf check
                if math.isfinite(yi):
                    ys.append(yi)
                else:
                    ys.append(None)  # Plotly ignora null/None entre puntos
            except Exception:
                ys.append(None)

        # Convertir a listas JSON para pasar al template
        context['x_json'] = mark_safe(json.dumps(xs.tolist()))
        context['y_json'] = mark_safe(json.dumps(ys))
        context['funcion'] = funcion
        context['c'] = c_text
        # mostrar resultado del límite (si se pudo)
        if limite_sym is not None:
            context['limite'] = str(limite_pretty)
        else:
            context['limite'] = "No disponible"

    return render(request, 'graficar_limites.html', context)
