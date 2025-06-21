# -*- coding: utf-8 -*-
# %%
from datetime import datetime, timezone
import math
from random import choice as rc
import requests
from playwright.sync_api import sync_playwright

from for_the_record import Lectura
from recordat import numero_a_diaSemana, numero_a_mes # conversiones

from constants import carpeta, apikeyOpenWeather # aqui guardo valores generales, como la ubicacion "carpeta" donde están todos los achivo

# API key de OpenWeather
API_KEY = apikeyOpenWeather # consiguete una


def tico(chat_id: int, lugar: str = None) -> str:
    '''
    esta sirve para que haga todo al meterle el usr.
    yo creo que voy a hacerlo con preferencia a las coordenadas, siento q me da más confianza
    
    :param chat_id: mm xd?
    :param lugar: si no se especifica, va por las coordenadas del usuario
    :type lugar: str
    :type chat_id: int
    '''

    # obtenemos las coordenadas del bruv
    l = Lectura(chat_id)
    lat,lon = l.coord
    usrLocation = l.lugar

    # obtenemos la data del clima
    if lugar:
        jsonWeather = obtener_pronostico(location=lugar)
    else:
        jsonWeather = obtener_pronostico(coordinates=(lat,lon))

    # ARMAR RETURNS DE ERROR, QUE AHORA ME DA PAJA
    if int(jsonWeather['cod']) == 404:
        return f'no encontré {lugar}'

    # limpiamos los datos del dia y la semana
    try:
        owo = Owo(jsonWeather)
        if not lugar:
            owo._misma_ciudad(usrLocation)
        datosDia = owo.arreglo_del_dia()
        datosSemana = owo.arreglo_5_dias()
    except:
        return f'problema: {(jsonWeather, lat, lon, lugar)}'


    # generamos la plantilla con el html
    html = generar_html(dataDia=datosDia, data5dias=datosSemana)

    # y hacemo el scrinchot, devolviendo la ruta al achivo
    return sacar_screenshot(html=html, nombreImagen=str(chat_id))

def sacar_screenshot(html: str, nombreImagen: str = 'img', file: bool = False):
    '''
    pa abrir el html y sacar el scrinchot, no pillé otra manera de hacerlo

    :param html: html
    :param nombreImagen: nombre de la imagen
    :param file: de que si el param "html" es un archivo (file), lo abrimos como texto
    :type html: str
    :type nombreImagen: str
    :type file: bool
    '''

    # si es file lo abrimos
    if file:
        html = open(html, 'r').read()
    
    # internec
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(device_scale_factor=2)
        page = context.new_page()

        # establecemos el html
        page.set_content(html)
        
        # encontramos lo q queremosss oh si
        page.wait_for_selector(".card")
        card = page.locator(".card")
        box = card.bounding_box()

        # hacemos que el tamaño de la ventana sea casi el de la tarjeta para q el scrinchot se vea más bonito y sacamos la foto
        page.set_viewport_size({"width": box['width']+27, "height": box['height']+27})
        path = f'{carpeta}/autoCache/weather_{nombreImagen}.png'
        page.screenshot(path=path)
        
        browser.close()
    
    return path

def obtener_pronostico(*, location: str = None, coordinates: tuple[float,float] = None) -> dict:
    '''
    extrae data en formato json de la api de openWeather

    :param location: lugar, si es q no se definen las coordenadas
    :param lat: latitud, siesq no se define el lugar
    :param lon: longitud, siesq no se define el lugar
    :type location: str
    :type lat: int
    :type lon: int
    '''

    # si es una o la otra elige una o la otra
    if coordinates:
        lat, lon = coordinates
        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
    if location:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric&lang=es"
    
    # devolvemos el json
    respuesta = requests.get(url)
    print(respuesta)
    return respuesta.json()

def generar_html(dataDia: dict, data5dias: dict) -> str:
    '''
    generar desde la planilla que ya tenemos, necesitamos:

    :param dataDia: diccionario con lo del dia
    :param data5dias: diccionario con lo de los 5 dias
    :type dataDia: dict
    :type data5dias: dict
    '''

    # quiza ir rotando los backgrounds, como segun el clima, o nose
    background = ['linear-gradient(17deg, #1e343b, #362727)', 'linear-gradient(50deg, #295562, #6a3333)', 'linear-gradient(100deg, #590755, #0d4144)', 'linear-gradient(to right, #590755, transparent), radial-gradient(circle at center, #917f09, #0d4144)'][0]

    # los paquetitos con los 5 dias de pronostico
    forecast_5_dias_html = ''.join([
        f'<div class="day"><b>{data5dias[dia]["name"]}</b> - - - {data5dias[dia]["maxmin"][0]}°C <br>•<br> {data5dias[dia]["maxmin"][1]}°C '
        f'<img src="https://openweathermap.org/img/wn/{data5dias[dia]["icon"]}.png" alt="logo clima"></div>'
        for dia, _ in list(data5dias.items())[:5]
        ])

    # graficos de temp, nubs y pop
    grafico_temp = f'''
        const ctx = document.getElementById('graficaTemps').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {dataDia['listHoras']},
                datasets: [{{
                    label: '°C',
                    data: {dataDia['temps']['listTemps']},
                    borderColor: 'rgba(255, 255, 132, 1)',
                    backgroundColor: 'rgba(255, 255, 132, 0.2)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ grid: {{ display: false }}, beginAtZero: false, ticks: {{ callback: value => value + ' °C', font: {{ size: 7 }} }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 7 }} }} }}
                }}
            }}
        }});
        '''
    
    grafico_nubs = f'''
        const ctx_2 = document.getElementById('graficaNubs').getContext('2d');
        new Chart(ctx_2, {{
            type: 'line',
            data: {{
                labels: {dataDia['listHoras']},
                datasets: [{{
                    label: '% Prob',
                    data: {dataDia['listNubs']},
                    borderColor: 'rgba(255, 255, 255, 1)',
                    backgroundColor: 'rgba(255, 255, 255, 0.3)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ grid: {{ display: true }}, max: 100, beginAtZero: true, ticks: {{ callback: value => value + ' %', font: {{ size: 5 }} }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 7 }} }} }}
                }}
            }}
        }});
        '''
    
    grafico_pops = f'''
        const ctx_2 = document.getElementById('graficaPops').getContext('2d');
        new Chart(ctx_2, {{
            type: 'line',
            data: {{
                labels: {dataDia['listHoras']},
                datasets: [{{
                    label: '% Prob',
                    data: {dataDia['pops']['listPops']},
                    borderColor: 'rgba(0, 255, 255, 1)',
                    backgroundColor: 'rgba(0, 255, 255, 0.3)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ grid: {{ display: true }}, max: 100, beginAtZero: true, ticks: {{ callback: value => value + ' %', font: {{ size: 5 }} }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 7 }} }} }}
                }}
            }}
        }});
        '''

    grafica2, titulo_grafica2, grafico_2 = ('graficaPops', 'Prob. Lluvia', grafico_pops) if dataDia['pops']['popGeneral'] else ('graficaNubs', 'Nubes', grafico_nubs) # si no llueve, nubes

    # html completo miamor
    html = f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Pronóstico del Tiempo</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <link href="https://fonts.googleapis.com/css2?family=Playwrite+RO&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: Arial, sans-serif; 
                    background: #191919f5; 
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    height: 100vh;
                    margin: 0;
                    }}
                .card {{ background: linear-gradient(50deg, #295562, #6a3333); 
                    border-radius: 30px; 
                    width: 277px; 
                    padding: 15px; 
                    box-shadow: 6px 6px 10px rgba(0, 0, 0, 0.3); 
                    text-align: center; 
                    }}
                .title {{ font-family: 'Playwrite RO', serif; 
                    padding: 1px;
                    font-size: 30px; 
                    font-weight: bold;
                    background-color: #fffefe34;
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 20px;
                    }}
                .mapa {{ overflow: hidden; 
                    margin-bottom: 5px; 
                    }}
                canvas {{ width: 100% !important; 
                    height: 100px!important; 
                    }}
                .subtitle {{ justify-content: 
                    space-between; 
                    }}
                .subtitile_text {{ font-size: 14px; 
                    text-align: center;
                    padding: 10px; 
                    color: #ffffffae; 
                    border-radius: 14px; 
                    }}
                .subsubtitle {{ justify-content: space-between; }}
                .subsubtitile_text {{ font-size: 8px; 
                    text-align: left; 
                    padding: 1px; 
                    color: #ffffff3d; 
                    }}
                .forecast {{ display: flex; 
                    justify-content: space-between; 
                    margin-top: 3px; 
                    }}
                .day {{ font-size: 14px; 
                    padding: 10px; 
                    text-align: center; 
                    background-color: #e5e2e20b; 
                    color: #ffffff62; 
                    border-radius: 16px; 
                    width: 33px; 
                    display: flex; 
                    flex-direction: column; 
                    align-items: center; 
                    }}
                .day b {{ text-align: left; 
                    color: #b2b0b0a9; 
                    }}
                .subtitile_text b {{ font-size: 16px; 
                    color: #f4f7f9c2; 
                    }}
                .parrafo {{ display: flex; 
                    justify-content: space-between; 
                    margin-top: 9px; 
                    }}
                .content {{ font-size: 14px; 
                    padding: 11px; 
                    background-color: #04040417; 
                    border-radius: 14px; 
                    text-align: justify; 
                    }}
                .grad-text {{ color: #fefefe77; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="title">{dataDia['textos']['city']}</div>
                <div class="subsubtitile">
                    <div class="subsubtitile_text"><b>Temperaturas</b></div>
                    </div>
                <div class="mapa"><canvas id="graficaTemps"></canvas></div>
                <div class="subsubtitile">
                    <div class="subsubtitile_text"><b>{titulo_grafica2}</b></div></div>
                <div class="mapa"><canvas id="{grafica2}"></canvas></div>
                <div class="subtitle">
                    <div class="subtitile_text">
                        <b>{dataDia['dia']['name']} {dataDia['dia']['numero']} de {dataDia['dia']['mes']}</b><br>
                        {dataDia['temps']['maxmin'][0]}°C ~ {dataDia['temps']['maxmin'][1]}°C — {dataDia['textos']['descripcion']}
                    </div></div>
                <div class="subsubtitile">
                    <div class="subsubtitile_text">Pronóstico próximos días:</div></div>
                <div class="forecast">
                    {forecast_5_dias_html}</div>
                <div class="parrafo">
                    <div class="content">
                        <span class="grad-text">
                            <i>{dataDia['textos']['parrafo']}</i>
                        </span>
                    </div></div>
            </div>
            <script>
                {grafico_temp}
                {grafico_2}
            </script>
        </body>
        </html>
        '''

    return html

def guardar_html_en_archivo(nombre_archivo: str, html: str) -> None:
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        f.write(html)

class Owo:
    def __init__(self, data: dict, auto: bool = True):
        '''
        iniciar esta picha la vaca mae q locura, a ver cuantas weas va a tocar arreglar

        :param data: el diccionario ql del openWeather para sacarle todo el juguitoo ssssslurp
        :type data: dict
        '''
        if type(data) == str:
            data = eval(data)

        self.dataDict = data

        if auto:
            self._info_general()
            self._info_5_dias()
            self._info_del_dia()

    def _misma_ciudad(self, ciudad_usr: str) -> bool:
        '''
        con esto se pretende arreglar que la API aveces falla
        con el nombre en ciudades remotas. Si el nombre que tenemos
        no coincide con e q dio la API, se cambia
        
        :param ciudad_usr: lugar guardado del usr
        :type ciudad_usr: str
        '''
        # si no calza, se cambia
        if self.city.lower() not in ciudad_usr.lower():
            self.city = ciudad_usr.split(',')[0].strip()
            return False
        return True

    def _max_min_temp(self, data: list, pod: str = 'd') -> tuple:
        '''
        pa obtener la maxima y minima del dia, 
        voy a ver si la hago de forma que solo obtenga la temp durante el dia

        :param data: la lista con todos los dicts con cada data
        :param pod: parte del dia: "d" dia, "n" noche, (day & night para los internacionales)
        :type data: list
        :type pod: str
        '''
        # parametros extremos para la comparativa
        params = [-999, 999]
        maxim = params[0]
        minim = params[1]

        # se comprueba si es de día o noche y se compara
        for item in data:
            if item['pod'] in pod:
                t_min_data = item['temp_min']
                t_max_data = item['temp_max']
                minim = t_min_data if t_min_data < minim else minim
                maxim = t_max_data if t_max_data > maxim else maxim
        

        # si no hubo data de día, probamos denoche
        if maxim == params[0] and minim == params[1]:
            maxim, minim = self._max_min_temp(data=data, pod='n')
        
        # el menor hacia abajo y el mayor hacia arriba
        maxim, minim = math.ceil(maxim), int(minim)

        self.MaxMinTempVals = (maxim, minim)
        return (maxim, minim)

    def filtro_data_dia(self, data: list) -> list:
        '''
        para tener toda la data solo del dia q queremos

        :param data: la lista con todos los dicts con data
        :type data: list
        '''
        dayList = []
        for item in data:
            # obtenemos la item
            date_data = self._timestamp(item['dt'])
            day_data = date_data.day

            # la agregamos si cumple
            if day_data == self.day:
                dayList.append(item)
        
        self.dayList = dayList
        return dayList

    def _timestamp(self, timestamp: int):
        '''
        :param timestamp: tiempo en unix
        :type timestamp: int
        '''
        return datetime.fromtimestamp(timestamp + self.ajusteHora, tz = timezone.utc)

    def _llueve(self, data: list) -> tuple:
        '''
        define el icono de lluvia si llueve, dandole prioidad a la lluvia de día

        :param data: lista q venga en el fomato del arreglo
        :type data: list
        '''

        self.llueveDia = False
        self.llueveNoche = False
        self.iconLluvia = None
        
        for item in data:
            if item['pop'] > 0 and item['pod'] == 'd':
                self.llueveDia = True
                self.iconLluvia = item['icon']
            
            if item['pop'] > 0 and item['pod'] == 'n':
                self.llueveNoche = True
                if not self.llueveDia:
                    self.iconLluvia = item['icon']
        
        return self.llueveDia, self.llueveNoche, self.iconLluvia

    def _icon(self, data: list) -> str:
        '''
        define el icono, dandole prioidad a la lluvia de día

        :param data: lista q venga en el fomato del arreglo
        :type data: list
        '''

        # dejemoslo basico por ahora
        icono = None
        for item in data:
            hora = item['hora']
            if 7 < hora < 14:
                icono = item['icon']
        
        d, n, i = self._llueve(data)
        if d or n:
            icono = i

        if icono != None:
            return icono
        else:
            return data[0]['icon']

    def arreglo_5_dias(self) -> dict:
        '''
        practicamente todo lo de los 5 dias
        '''
        dictProvisional5 = {}
        dict5 = {}
            
        # creamos el dict con los 5 dias
        for stamp in self.fiveDayUnix:
            date_info = self._timestamp(stamp)
            numDia = date_info.day

            diaSemana = numero_a_diaSemana(date_info.weekday())[0:3]

            indice = numDia - self.day
            if numDia == self.day:
                diaSemana = 'Hoy'

            # dict
            dictProvisional5[indice] = {'dia': {'num': numDia, 'semana': diaSemana}, 'weather': []}
        

        # recorremos la otra info y la anadimos al dict de antes
        for i, stamp in enumerate(self.fiveDayUnix):
            date_info = self._timestamp(stamp)
            numDia = date_info.day

            indice = numDia - self.day
            # dict
            dictProvisional5[indice]['weather'].append({
                't': self.fiveDayTemps[i],
                'temp_min': self.fiveDayTMin[i],
                'temp_max': self.fiveDayTMax[i],
                'stamp': stamp, 
                'pod': self.fiveDayPOD[i], 
                'pop': self.fiveDayPops[i],
                'hum': self.fiveDayHum[i],
                'pressure': self.fiveDayPressures[i],
                'icon': self.fiveDayIcons[i],
                'hora': date_info.hour})
        
        # creamos el diccionario final. Tomamos el dia, maximo y minimo de T, y el iconito
        for item in dictProvisional5:
            dictItem = dictProvisional5[item]
            maxmin = self._max_min_temp(dictItem['weather'])
            diaSemana = dictItem['dia']['semana']
            if dictItem['dia']['num'] == self.day:
                diaSemana = 'Hoy'
            icono = self._icon(dictItem['weather'])

            dict5[item] = {'name': diaSemana, 'maxmin': maxmin, 'icon': icono}
        
        self._dictProvisional5 = dictProvisional5
        self.dict5 = dict5
        return self.dict5
 
    def arreglo_del_dia(self) -> dict:
        '''
        todo lo de hoy, arregladito para usarlo con el html
        '''
        # sobre la fecha
        dateData = self._timestamp(self.dayUnix[0])
        diaNumero = self.day
        diaSemana = numero_a_diaSemana(dateData.weekday()).capitalize()
        diaMes = numero_a_mes(dateData.month)
        listHoras = [f'{self._timestamp(stamp).hour}:{self._timestamp(stamp).minute:02}' for stamp in self.dayUnix]

        # temps
        listMaxMin = []
        for num, tempMax in enumerate(self.dayTMax):
            tempMin = self.dayTMin[num]
            pod = self.dayPOD[num]
            d = {'pod': pod, 'temp_min': tempMin, 'temp_max': tempMax}
            listMaxMin.append(d)
        
        listTemps = [round(n,1) for n in self.dayTemps]
        listPops = [int(n*100) for n in self.dayPops]
        listNubs = [int(n) for n in self.dayClouds]
        
        maxmin = self._max_min_temp(listMaxMin)
        
        # data de todo, para las redacciones
        sunset = self._timestamp(self.sunset)
        sunsetHora = f'{sunset.hour}:{sunset.minute:02}'
        sunrise = self._timestamp(self.sunrise)
        sunriseHora = f'{sunrise.hour}:{sunrise.minute:02}'

        infoViento = self._max_vientos(self.dayWindsSpeed, self.dayWindsDeg) # (velText, palabraVEL, palabraDeg, palabraPOD)
        infoHumedad = self._max_humidity(self.dayHum)
        textoLluvia, popGeneral = self._info_lluvia(self.dayPops)
        infoNubes = self._info_nubes(self.dayClouds)

        descripcion = rc(self.dayDescriptions)

        textoDeInicio = rc(['Hoy esperamos cielo', 'Para hoy tenemos un cielo', 'Tendremos un cielo', 'Estará', 'El cielo estará'])

        parrafo = f'''
            {textoDeInicio} {infoNubes} con {infoViento[1]}{infoViento[0]} hacia el {infoViento[2]}{infoViento[3]}.\n 
            Una {infoHumedad[1]} humedad máxima de {infoHumedad[0]}%. 
            Amanece a las {sunriseHora}, y atardecerá a las {sunsetHora}.\n{textoLluvia.capitalize()}.'''
        
        dictDia = {
            'dia': {'numero': diaNumero, 
                    'name': diaSemana, 
                    'mes': diaMes}, 
            'textos': {'descripcion': descripcion, 
                       'parrafo': parrafo, 
                       'city': self.city}, 
            'temps': {'maxmin': maxmin, 
                      'listTemps': listTemps}, 
            'pops': {'listPops': listPops,
                     'popGeneral': popGeneral},
            'listNubs': listNubs,
            'listHoras': listHoras}
        
        return dictDia

    def _info_nubes(self, data: list) -> str:
        '''
        como estará el cielo en cualidad nubistica

        :param data: lista de las nubes
        :type data: list
        '''
        # redactar segun el %
        def prob_a_palabra(val: int) -> str:
            if val <= 10:
                return rc(['despejado', 'claro', 'sin nubes'])
            elif val <= 30:
                return rc(['con un par de nubecitas', 'casi ni nublado'])
            elif val <= 60:
                return rc(['un poco nublado', 'algo nublado', 'nubladito'])
            else:
                return rc(['nublado', 'muy nublado', 'tapado en nubes', 'blanco, o gris'])
        
        dia = [0]

        # guardamos solo los % de día
        for n, poc in enumerate(data):
            if self.dayPOD[n] == 'd':
                dia.append(poc)
        
        # humanizamos
        maxDia = max(dia)
        palabraNube = prob_a_palabra(maxDia)
        return palabraNube

    def _info_lluvia(self, data: list) -> str:
        '''
        redactamos segun las probabilidades de lluvia, por lo general no me gusta devolver textos ya armados pero weno
        
        :param data: lista de las humedades
        :type data: list
        '''
        # redactar segun la prob
        def prob_a_palabra(val: int) -> str:
            if val == 0:
                return 'no llueve'
            elif val <= 30:
                return 'es un poco probable que llueva'
            elif val <= 60:
                return 'posiblemente llueve'
            elif val <= 80:
                return 'es muy probable que llueva'
            else:
                return 'llueve, seguro'

        dia = [0]
        noche = [0]

        # convertimos a % y guardamos las probs segun de noche o dia
        for n, pop in enumerate(data):
            pop = int(pop*100)
            if self.dayPOD[n] == 'd':
                dia.append(pop)
            else:
                noche.append(pop)

        # maxs xd
        maxDia = max(dia)
        maxNoche = max(noche)

        # cuándo en el transcurso del dia
        horaDiaLluvia = self._timestamp(self.dayUnix[dia.index(maxDia)]).hour
        if horaDiaLluvia >= 14:
            textoHora = 'por la tarde'
        else:
            textoHora = 'durante el dia'

        # redactamos la risposta
        palabraProbDia = prob_a_palabra(maxDia)
        palabraProbNoche = prob_a_palabra(maxNoche)
        popGeneral = (maxDia+maxNoche)/2
        
        redaccion = f'{palabraProbDia} {textoHora}, y de noche {palabraProbNoche}'
        if palabraProbNoche == palabraProbDia:
            redaccion = palabraProbNoche
        
        return redaccion, popGeneral

    def _max_humidity(self, data: list) -> tuple:
        '''
        simple as that

        :param data: lista de las humedades
        :type data: list
        '''
        maxHum = max(data)
        
        # redactar segun el %
        def clasificar_humedad(humedad):
            if humedad < 30:
                return rc(['suavecisima','ignorable','nula','mísera','insignificante y bella'])
            elif 30 <= humedad <= 60:
                return rc(['piola','coherente','decente','agradable','sensata','bonita'])
            elif 60 < humedad <= 80:
                return rc(["buena",'notable','juguetona','intrusa'])
            else:
                return rc(["babosa",'mala','súper','insensata','pegajosa','bien potente','#saborTropical'])
        
        textHum = clasificar_humedad(maxHum)

        return (maxHum, textHum)

    def _max_vientos(self, speeds: list, degs: list) -> tuple:
        '''
        devuelve la velocidad de viento max, y la dirección respectiva

        :param speeds: lista con las velocidades 
        :param degs: lista con los angulos
        :type speeds: list
        :type degs: list
        '''
        direcciones = ['norte', 'nordeste', 'este', 'sureste', 'sur', 'suroeste', 'oeste', 'noroeste']

        # redactar segun la fuerza
        def fuerza_a_palabra(val: int) -> str:
            if val < 6:
                return rc(['aire calmo', 'viento calmo', 'un susurro de aire'])
            elif val < 12:
                return rc(['una brisa ligera', 'un susurro de aire', 'viento calmo', 'una brisita'])
            elif val < 20:
                return rc(['una brisa suave', 'una brisita', 'un airecito'])
            elif val < 29:
                return rc(['una brisa moderada', 'su airecito'])
            elif val < 39:
                return rc(['una brisa fresca', 'vientecito', 'viento que sopla'])
            elif val < 50:
                return rc(['viento fuerte', 'un viento que sopla con ganas'])
            else:
                return rc(['vientos muy fuertes', 'un viento que sopla con ganas'])

        # valores, viento a km/h
        vel = max(speeds)
        deg = degs[speeds.index(vel)]
        pod = self.dayPOD[speeds.index(vel)]
        vel = round(vel * 3.6)
        
        # fuerteza del viento
        palabraVEL = fuerza_a_palabra(vel)

        # direccion del viento fuerte
        indice = round(deg / 45) % 8
        palabraDeg = direcciones[indice]

        # en q momento del dia
        if pod == 'd':
            palabraPOD = ''
        if pod == 'n':
            palabraPOD = ' esta noche'

        # pa decir 2 km/h mejo no decir nada
        velText = ' a ' + str(vel) + ' km/h'
        if vel < 12:
            velText = ''

        return (velText, palabraVEL, palabraDeg, palabraPOD)

    def _info_general(self, data: dict = {}):
        if not data:
            data = self.dataDict
        
        self.ajusteHora = data['city']['timezone']
        self.day = self._timestamp(data['list'][0]['dt']).day
        self.sunrise = data['city']['sunrise']
        self.sunset = data['city']['sunset']
        self.city = data['city']['name']

    def _info_5_dias(self, data: dict = {}):
        if not data:
            data = self.dataDict

        self.fiveDayUnix = []
        self.fiveDayTMin = []
        self.fiveDayTMax = []
        self.fiveDayTemps = []
        self.fiveDayIcons = []
        self.fiveDayPressures = []
        self.fiveDayHum = []
        self.fiveDayDescriptions = []
        self.fiveDayPops = []
        self.fiveDayWindsSpeed = []
        self.fiveDayWindsDeg = []
        self.fiveDayClouds = []
        self.fiveDayPOD = []

        for item in data['list']:
            self.fiveDayTMin.append(item['main']['temp_min'])
            self.fiveDayTMax.append(item['main']['temp_max'])
            self.fiveDayUnix.append(item['dt'])
            self.fiveDayTemps.append(item['main']['temp'])
            self.fiveDayIcons.append(item['weather'][0]['icon'])
            self.fiveDayPressures.append(item['main']['pressure'])
            self.fiveDayHum.append(item['main']['humidity'])
            self.fiveDayDescriptions.append(item['weather'][0]['description'])
            self.fiveDayPops.append(item['pop'])
            self.fiveDayPOD.append(item['sys']['pod'])
            self.fiveDayWindsSpeed.append(item['wind']['speed'])
            self.fiveDayWindsDeg.append(item['wind']['deg'])
            self.fiveDayClouds.append(item['clouds']['all'])

    def _info_del_dia(self, data: dict = {}):
        if not data:
            data = self.dataDict
        
        self.dayUnix = []
        self.dayTemps = []
        self.dayTMin = []
        self.dayTMax = []
        self.dayIcons = []
        self.dayPressures = []
        self.dayHum = []
        self.dayDescriptions = []
        self.dayPops = []
        self.dayWindsSpeed = []
        self.dayWindsDeg = []
        self.dayClouds = []
        self.dayPOD = []


        for item in data['list']:
            if self._timestamp(item['dt']).day == self.day:
                self.dayPOD.append(item['sys']['pod'])
                self.dayUnix.append(item['dt'])
                self.dayTemps.append(item['main']['temp'])
                self.dayTMin.append(item['main']['temp_min'])
                self.dayTMax.append(item['main']['temp_max'])
                self.dayIcons.append(item['weather'][0]['icon'])
                self.dayPressures.append(item['main']['pressure'])
                self.dayHum.append(item['main']['humidity'])
                self.dayDescriptions.append(item['weather'][0]['description'])
                self.dayPops.append(item['pop'])
                self.dayWindsSpeed.append(item['wind']['speed'])
                self.dayWindsDeg.append(item['wind']['deg'])
                self.dayClouds.append(item['clouds']['all'])

# %%
