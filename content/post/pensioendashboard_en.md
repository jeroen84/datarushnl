+++
date = 2020-05-26T09:00:00Z
lastmod = 2020-05-26T09:00:00Z
author = "Jeroen van de Erve"
title = "Pension Dashboard"
description = "View the current situation of the pension funds ABP, PFZW, PMT, and BPF Bouw in a clear dashboard"
tags = ["pension funds", "funding ratio", "abp", "pfzw", "python", "data science"]
# feature = "<no value>"
+++

The [pension dashboard](https://dashboards.datarush.nl/pensioendashboard) provides an overview of the current financial status of the pension funds ABP, PFZW, PMT, and BPF Bouw. This dashboard uses public data sources and open-source software. Various techniques are applied for retrieving and processing the data, including web scraping and APIs. Machine learning techniques are used for forecasting the funding ratios. Software such as Python, Azure Web Apps, Plotly, and Dash are used, all in a fully automated environment. The source code is available on [Github](https://github.com/jeroen84/datarush-pensioendashboard)!

Funding ratios are published only once a month by the funds, and only about two weeks after the end of the month. This dashboard presents an estimate of the funding ratio from the last published figure. The estimate uses five market indicators, see the second and third graphs. The number of funds in the overview will be expanded.

The historical funding ratios have been obtained from the websites of the pension funds. For estimating the funding ratios, a linear regression model is used, with test and training sets. The estimate contains many statistical assumptions and limitations. Deviations from the published figures will occur. Therefore, the estimates should be interpreted as an indication of the direction in which the funding ratios are developing.
