+++
date = 2020-05-26T09:00:00Z
lastmod = 2020-05-26T09:00:00Z
author = "Jeroen van de Erve"
title = "Pensioendashboard"
description = "Bekijk de actuele situatie van de pensioenfondsen ABP, PFZW, PMT en BPF Bouw in een overzichtelijk dashboard"
tags = ["pensioenfondsen", "dekkingsgraad", "abp", "pfzw", "python", "data science"]
# feature = "<no value>"
+++

Het [pensioendashboard](https://dashboards.datarush.nl/pensioendashboard) geeft een overzicht van de actuele financiële stand van zaken van de pensioenfondsen ABP, PFZW, PMT en BPF Bouw. Voor dit dashboard wordt gebruik gemaakt van openbare databronnen en opensource software. Verschillende technieken worden toegepast voor het binnenhalen en bewerken van de data, onder andere webscraping en API's. Voor de prognose van de dekkingsgraden worden machine learning technieken toegepast. Qua software wordt gebruik gemaakt van onder meer Python, Azure Web Apps, Plotly en Dash. Dit alles in een volledig geautomatiseerde omgeving. De broncode is op [Github](https://github.com/jeroen84/datarush-pensioendashboard) geplaatst!

Dekkingsgraden worden slechts eenmaal per maand gepubliceerd door de fondsen, en pas circa twee weken na het einde van de maand. Dit dashboard presenteert een inschatting van de dekkingsgraad vanaf het laatst gepubliceerde cijfer. Voor de inschatting wordt gebruik gemaakt van vijf marktindicatoren, zie de tweede en derde grafiek. Het aantal fondsen in het overzicht zal uitgebreid worden.

De historische dekkingsgraden zijn verkregen van de websites van de pensioenfondsen. Voor de schatting van de dekkingsgraden wordt gebruik gemaakt van een lineair regressiemodel, waarbij test en training sets worden gebruikt. De schatting bevat statistisch gezien vele aannames en beperkingen. Afwijkingen ten opzichte van de gepubliceerde cijfers zullen er zijn. Daarom dienen de schattingen geïnterpreteerd te worden als een richting waarop de dekkingsgraden zich ontwikkelen.

