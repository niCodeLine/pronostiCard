# pronostiCard
What I use in my AI (Artificial Idiot) to get the weather of my, or any location.


## Usage

Since the package is called _pornos_ (my keyboard is half working and I misspelled *pronos*), I call the
function _tico_, forming then the word _pronos.tico_ (or _pornos.tico_ in this case), meaning forecast in spanish.  
  

It checks if the input _lugar_ (place) is a name or the coordinates of some place and continues with:

```python
jsonData = obtener_pronostico(location = 'mackay')
```

or

```python
float: lat = -21.1408
float: lon = 149.1851

jsonData = obtener_pronostico(coodinates = (lat, lon))
```

we proceed by calling the class **Owo** to clean the data getting the forcast of today and the next 5 days:

```python
owo = Owo(jsonData)

datosDia = owo.arreglo_del_dia()
datos5Dias = owo.arreglo_5_dias()
```

from here we create the HTML script, and take the screenshot of the card:

```python
html = generar_html(dataDia=datosDia, data5dias=datos5Dias)

sacar_screenshot(html=html)
```


## Result

![result 1](images/test_Bundaberg.png)
![result 1](images/test_Mackay.jpg)

Very cloudy at Mackay as we can see.

## Features

- **Considers Uslessness of Data**: If the average of the probabilty of rain is 0, it changes the second graph
showing the percentage of clouds instead.
- **Redaction**: It gets random generated responses explaining the weather to give it a more natural feeling.
- **Beautiful**: Nice colors.


## Contributions

Contributions are welcome! If you have improvements or fixes, please send a pull request or open an issue in the GitHub repository.

## License

This project is licensed under the MIT License. Do whatever you want.

## Contact

Nico Spok - nicospok@proton.me
GitHub: niCodeLine
