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
        # recibir listas (compatibilidad con name="funcion[]" )
        funciones = request.POST.getlist('funcion[]')
        cs = request.POST.getlist('c[]')

        # compatibilidad: si no vienen como listas, intentar obtener single values
        if not funciones:
            single_f = request.POST.get('funcion', '')
            if single_f is not None and single_f.strip() != '':
                funciones = [single_f.strip()]
        if not cs:
            single_c = request.POST.get('c', '')
            if single_c is not None and single_c.strip() != '':
                cs = [single_c.strip()]

        # si aún no hay listas válidas, usar defaults (evita crash)
        if not funciones:
            funciones = ['']
        if not cs:
            # si no se envía c, por cada función usar '0'
            cs = ['0'] * len(funciones)

        # asegurarse de que cs y funciones tienen misma longitud
        if len(cs) < len(funciones):
            # rellenar cs con '0' si faltan
            cs += ['0'] * (len(funciones) - len(cs))
        elif len(funciones) < len(cs):
            funciones += [''] * (len(cs) - len(funciones))

        # símbolo independiente
        x = sp.symbols('x')

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
        }

        resultados = []
        global_errors = []

        for idx, (funcion, c_text) in enumerate(zip(funciones, cs)):
            funcion = (funcion or '').strip()
            c_text = (c_text or '').strip() or '0'

            if funcion == '':
                # ignorar entradas vacías
                continue

            # parseo simbólico
            try:
                expr = sp.sympify(funcion, locals=allowed)
                c_sym = sp.sympify(c_text, locals=allowed)
            except Exception as e:
                # almacenar error por función y continuar
                resultados.append({
                    'funcion': funcion,
                    'c': c_text,
                    'limite': None,
                    'x_json': None,
                    'y_json': None,
                    'error': f"Error al parsear la función o c: {e}"
                })
                continue

            # calcular límite simbólico (si puede)
            limite_sym = None
            limite_pretty = None
            try:
                limite_sym = sp.limit(expr, x, c_sym)
                try:
                    limite_pretty = sp.N(limite_sym)
                except Exception:
                    limite_pretty = limite_sym
            except Exception as e:
                # No detener, solo marcar que no se pudo calcular simbólicamente
                limite_sym = None
                limite_pretty = None
                limite_error_msg = f"No se pudo calcular límite simbólico: {e}"
            else:
                limite_error_msg = None

            # convertir c a número para rango
            try:
                c_val = float(sp.N(c_sym))
            except Exception:
                c_val = 0.0

            # crear rango de x centrado en c
            x_min = c_val - 5
            x_max = c_val + 5
            N = 600
            xs = np.linspace(x_min, x_max, N)

            # convertir expresión a función numérica
            try:
                f_num = sp.lambdify(x, expr, modules=['numpy', 'mpmath'])
            except Exception as e:
                resultados.append({
                    'funcion': funcion,
                    'c': c_text,
                    'limite': str(limite_pretty) if limite_pretty is not None else None,
                    'x_json': None,
                    'y_json': None,
                    'error': f"No se pudo convertir la función a numérica: {e}"
                })
                continue

            # evaluar numéricamente
            ys = []
            for xi in xs:
                try:
                    yi = f_num(xi)
                    # tratar números complejos (si vienen)
                    if hasattr(yi, 'real') and hasattr(yi, 'imag'):
                        if abs(yi.imag) > 1e-12:
                            yi = float('nan')
                        else:
                            yi = float(yi.real)
                    else:
                        # intento de casting seguro para tipos numpy scalar
                        yi = float(yi)
                    if math.isfinite(yi):
                        ys.append(yi)
                    else:
                        ys.append(None)
                except Exception:
                    ys.append(None)

            # preparar salida JSON (listas)
            try:
                x_list = xs.tolist()
            except Exception:
                x_list = [float(v) for v in xs]

            resultados.append({
                'funcion': funcion,
                'c': c_text,
                'limite': str(limite_pretty) if limite_pretty is not None else None,
                'x_json': x_list,
                'y_json': ys,
                'error': limite_error_msg
            })

        # si no hay resultados válidos, añadir mensaje
        if not resultados:
            context['error'] = "No se recibieron funciones válidas."
            return render(request, 'graficar_limites.html', context)

        # añadir al contexto la lista de resultados (cada uno con sus datos)
        context['resultados'] = resultados

        # compatibilidad con una sola función (template antiguo)
        if len(resultados) == 1:
            r = resultados[0]
            context['funcion'] = r['funcion']
            context['c'] = r['c']
            context['limite'] = r['limite'] or "No disponible"
            # poner x_json/y_json en formato seguro para el template (json)
            if r.get('x_json') is not None:
                context['x_json'] = mark_safe(json.dumps(r['x_json']))
            if r.get('y_json') is not None:
                context['y_json'] = mark_safe(json.dumps(r['y_json']))

        # también exponer 'resultados_json' para que puedas iterar y usar en JS si quieres
        # (ya contiene listas Python; si las necesitas como JSON en el template, conviértelas)
        # convertir arrays a JSON seguros para inyectar en template si es necesario
        safe_results = []
        for r in resultados:
            safe_results.append({
                'funcion': r['funcion'],
                'c': r['c'],
                'limite': r['limite'],
                'x_json': json.dumps(r['x_json']) if r.get('x_json') is not None else None,
                'y_json': json.dumps(r['y_json']) if r.get('y_json') is not None else None,
                'error': r.get('error')
            })
        context['resultados_json'] = safe_results

    return render(request, 'graficar_limites.html', context)
