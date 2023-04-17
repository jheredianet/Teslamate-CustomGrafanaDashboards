# TeslaMate Custom Grafana Dashboards

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Stargazers][stars-shield]][stars-url][![Contributors][contributors-shield]][contributors-url][![Forks][forks-shield]][forks-url][![Issues][issues-shield]][issues-url][![Discussions][discussions-shield]][discussions-url][![MIT License][license-shield]][license-url]

This is a project with **Custom Grafana Dashboards**, created especially to work with a **Teslamate installation**. So the main requirement for these dashboards to work, is to have a **[Teslamate](https://docs.teslamate.org/)** running instance.

## TeslaMate

**[Teslamate](https://docs.teslamate.org/)** is a powerful, self-hosted data logger for your Tesla.

- Written in **[Elixir](https://elixir-lang.org/)**
- Data is stored in a **Postgres** database
- Visualization and data analysis with **Grafana**
- Vehicle data is published to a local **MQTT** Broker

___

## How to Auto-import these Custom Dashboards

In order to auto-import all the dashboard files from this repository, considering that your are using the official  [Teslamate Docker install](https://docs.teslamate.org/docs/installation/docker) documentation guide, proceed as follows.

**Note:** If you are using Teslamate without Docker you may skip these section and proceed to import manually.

- The following command will clone the source files from this repository. This should be run in an appropriate directory within which you would like to keep it. You should also record this path and provide it later in the following steps. To keep it easy, you may run this your home path (~/) or modify it accordingly.

```bash
git clone https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards.git
```

- Edit your Teslamate "docker-compose.yml" file and add these two new lines at the end of the "volumes" section of the grafana container

```yaml
services:
  ...
  ...
  grafana:
    ...
    ...
    volumes:
      - teslamate-grafana-data:/var/lib/grafana
      - ~/Teslamate-CustomGrafanaDashboards/customdashboards.yml:/etc/grafana/provisioning/dashboards/customdashboards.yml
      - ~/Teslamate-CustomGrafanaDashboards/dashboards:/TeslamateCustomDashboards
```

- Save your file and then **recreate** Grafana container (docker-compose up -d)
- Browse the Grafana Dashboards from the Web and you should have a new "TeslaMate Custom Dashboards" folder

## Using other path for repository

Attention! On some VPS from certain providers like Google GCC, the user running docker engine is not the current user so it's home folder is different, or maybe you just want to use a specific folder for your data. If this is the case, it's better to use the **full path** of the repository where you cloned it, instead of using the home path of the current user (~/). So, be sure to modify the path of the volumes section accordingly, as the sample given below:

```yaml
services:
  ...
  ...
  grafana:
    ...
    ...
    volumes:
      - teslamate-grafana-data:/var/lib/grafana
      - /some/path/Teslamate-CustomGrafanaDashboards/customdashboards.yml:/etc/grafana/provisioning/dashboards/customdashboards.yml
      - /some/path/Teslamate-CustomGrafanaDashboards/dashboards:/TeslamateCustomDashboards
```

## How to update the Dashboards

If you want to be sure that you are using the latest version of the Dashboards:

- Pull again from the repository

```bash
git -C ~/Teslamate-CustomGrafanaDashboards pull
```

- Then **restart** Grafana container (docker-compose restart grafana)

___

## How to manually import these custom dashboards

The following steps let you import the JSON files into your setup:

- On Grafana (from Teslamate instance), Browse Dashboards then Import...
- Upload JSON file or import via panel json by pasting the raw content of te JSON file.
- On the next screen you may name the dashboard as you wish or accept the suggested one.
- Try to keep UID as it is, because it could be linked inside the dashboard and to avoid duplicates UIDs.
- Then select the appropiate Teslamate datasource from the available droplist.
- Finally, press the "Import" button

___

## Screenshots

### [Battery Health](./dashboards/BatteryHealth.json)

This dashboard is meant to have a look of the Battery health based on the data logged in Teslamate.
So, the more data you have logged from your brand new car the better.

**Degradation** is just an estimated value to have a reference, measured on **usable battery level** of every charging session in the last month, with enough kWh added (in order to avoid dirty data from the sample), calculated according to the rated efficiency of the car. On the other hand, you'll see a plotly chart that represents the evolution of the car's battery capacity during its entire lifetime.

Finally, there is an important improvement for those who have not used Teslamate since they got their car, or for those who have bought it second hand. Now it is possible to set the max range to 100% and the battery capacity of the car battery when it was new in order to get an accurate and better estimation.

![Battery Health](./screenshots/BatteryHealth.png)

### [Browse Charges](./dashboards/BrowseCharges.json)

This dasboard is used to browse your charges by Geofence, Location, Type, Cost and Duration in order to have an accurate Total of kWh added and their respective costs.

![Browse Charges](./screenshots/BrowseCharges.png)

### [Charging Costs Stats](./dashboards/ChargingCostsStats.json)

This dashboard is meant to have a look of all the charges in a given period (last 10 years by default).
You can see the distance driven, number of charges, total charging cost, etc., both in summary or in
separated lists.

You can expand/collapse the rows as needed.

From the Monthly Stats row, you will have a table with links to other Teslamate Dashboards to have a look on a specific period, charge or trip.

![Charging Costs Stats](./screenshots/ChargingCostsStats.png)

### [Charging Curve Stats](./dashboards/ChargingCurveStats.json)

This dashboard is meant to have a look of the charging curve sessions on Tesla Supercharges or other Fast Charging Station. Also, you can see number of fast charging sessions you've done on each type of chargers and the count of max power (kW) reached on a session as shown in the following example.

![Charging Curve Stats](./screenshots/ChargingCurveStats.png)

### [Continuous Trips](./dashboards/ContinuousTrips.json)

This dashboard has a table with all the trips you've made between charges sesions, so you can browse the longest or shortest mileage you travel.

You may also take a look to a specific trip from the initial charge session (before the trip) to the end of the of the charge session (after the trip), through the link in the first column that will take you to the TeslaMate Trips dashboard.

![Continuous Trips](./screenshots/ContinuousTrips.png)

### [Current Charge View](./dashboards/CurrentChargeView.json)

Load this dashboard to while you are in a charging sesion. When you open this dashboard it will show the last 15 minutes, but you should click the "Current Charge" button at the top right corner, to enter in Kiosk mode:

- If you are charging, you will see the information from the start time of the current charge session until now and it will refesh automatically every 30 seconds.
- If you are just browsing (not charging) you will see the information of the last charge session.  

![Current Charge View](./screenshots/CurrentChargeView.png)

### [Current Drive View](./dashboards/CurrentDriveView.json)

This is a special dashboard to load while driving. When you open this dashboard it will show the last 15 minutes, but you should click the "Current Drive" button at the top right corner, to enter in Kiosk mode:

- If you are driving, you will see the information from the start time of the current drive until now and it will refesh automatically every 30 seconds.
- If you are just browsing (not driving) you will see the information of the last drive.  

![Current Drive View](./screenshots/CurrentDriveView.png)

### [Current State](./dashboards/CurrentState.json)

This dasboard is just to see the current state of the car with the last data recorded by TeslaMate.

Additionally, you can see the states stats of the selected period.

![Current State](./screenshots/CurrentState.png)

### [Mileage Stats](./dashboards/MileageStats.json)

With this dashboard you may analize your mileage and number of drives by year, month, week or day.

The dashboard shows a table with the selected period, time driven, distance, number of drives and efficiency then a bar chart to have a better look for comparison.  

![Mileage Stats](./screenshots/MileageStats.png)

### [Tracking Drives](./dashboards/TrackingDrives.json)

This dashboard is meant to analize a drive based on a date you select, then you can pass the pointer over the lines in graph
to see data details and a blue point in the map tranking the route. With this option you can analized a specific point location in the map,
to see the speed, power, SOC, elevation and if battery heater was on.

Be aware that the drive you select in the dropdown list from the top could be outside the time range of the Timeline graph,
if its the case you have to click on the "Zoom to data" button on the graph in order to update it.

Tip: On Grafana you can press "h" to get a keyboard shortcuts if you want to change the current Zoom out time range or use the mouse to select/change the time range.

![Tracking Drives](./screenshots/TrackingDrives.gif)

## Contributing

The following dashboards, queries and design are the result of many tests and hours of work.
Feel free to take them for your own personal use.

If you are able to contibute or improve this project just fork the repository and make a pull request. I'll really apreciate any enhancement or suggestion.

Do not take the dashboards much less upload or merge them to other repositories as if the original idea were yours, nor do you share it on social media without mentioning the author. Please, **respect the ingenuity and work of others**. Enjoy!

## Donations

|     |     |
| --- | --- |
| If you like my work and want to support me, buying me a coffee would be greatly appreciated! Your support helps me to keep creating and improving these dashboards. Thank you! | [![Paypal Donate](https://img.shields.io/badge/Donate-PayPal-ff69b4.svg)](https://www.paypal.com/donate/?business=MAWY99TACEXSU&no_recurring=0&currency_code=EUR) |
| Other way to support me is to use [my referral link](https://ts.la/juancarlos32618) to purchase a Tesla product and get Credits you can redeem for exclusive awards like Supercharging miles, merchandise, and accessories. | [![Tesla referral link](./screenshots/tesla.png)](https://ts.la/juancarlos32618) |
|     |     |

## Credits

- Author: [Juan Carlos Heredia](https://infoinnova.net/contacto/)
- Based on/forked from [Adrian Kumpf](https://github.com/adriankumpf/teslamate) original code, with improvement of custom Grafana Dashboards (see [contributions history](https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards/graphs/contributors)).

## License

Licensed under the [MIT license](./LICENSE).

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/jheredianet/Teslamate-CustomGrafanaDashboards.svg?style=for-the-badge
[contributors-url]: https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/jheredianet/Teslamate-CustomGrafanaDashboards.svg?style=for-the-badge
[forks-url]: https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards/network/members
[stars-shield]: https://img.shields.io/github/stars/jheredianet/Teslamate-CustomGrafanaDashboards.svg?style=for-the-badge
[stars-url]: https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards/stargazers
[issues-shield]: https://img.shields.io/github/issues/jheredianet/Teslamate-CustomGrafanaDashboards.svg?style=for-the-badge
[issues-url]: https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards/issues
[discussions-shield]: https://img.shields.io/github/discussions/jheredianet/Teslamate-CustomGrafanaDashboards.svg?style=for-the-badge
[discussions-url]: https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards/discussions
[license-shield]: https://img.shields.io/github/license/jheredianet/Teslamate-CustomGrafanaDashboards.svg?style=for-the-badge
[license-url]: ./LICENSE
