# TeslaMate Custom Grafana Dashboards

### Last release: [v2026.10.15](https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards/releases/)

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

## Italian localized dashboards

The original English dashboard JSON files remain unchanged. An Italian locale pack is available and can be used to generate localized copies with the same dashboard UIDs and unchanged query/technical values.

Generate the Italian dashboards:

```bash
python3 scripts/generate_localized_dashboards.py \
  --pack i18n/it.json \
  --output dashboards-localized/it
```

To auto-import the Italian copies instead of the English originals, use the generated directory in the Grafana volume mapping:

```yaml
services:
  grafana:
    volumes:
      - teslamate-grafana-data:/var/lib/grafana
      - ~/Teslamate-CustomGrafanaDashboards/customdashboards.yml:/etc/grafana/provisioning/dashboards/customdashboards.yml
      - ~/Teslamate-CustomGrafanaDashboards/dashboards-localized/it:/TeslamateCustomDashboards
```

After pulling repository updates, run the generator again before restarting Grafana. The locale pack covers dashboard titles, panel titles, labels, legends, tooltips, descriptions and display aliases while keeping variables, datasource identifiers and query values intact.

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

- Then **restart** Grafana container

```bash
docker compose restart grafana  
```

Or (if you are using a previous docker version)

```bash
docker-compose restart grafana  
```

## How to use these Custom Dashboards

In order to use these dashboards, once imported, you may want to go to the Grafana "Browse" option (from the left vertical bar), from there you will see a new folder with the imported dashboards.

![Browse](./screenshots/help/browseoption.png) ![Custom Dashboards](./screenshots/help/customdasboardfolder.png)

This Custom Dashboards have a special label so they don't get mixed up with the Teslamate defaults dashboards to distinguish easier and group together. When you are in a Custom Dashboard you will see in the upper right corner, a drop-down button from  you may access the rest dashboards as well.

![DropDown](./screenshots/help/dropdownbutton.png)
___

## How to manually import these custom dashboards

The following steps let you import the JSON files into your setup if you don't want to auto-import them:

- On Grafana (from Teslamate instance), Browse Dashboards then Import...
- Upload JSON file or import via panel json by pasting the raw content of te JSON file.
- On the next screen you may name the dashboard as you wish or accept the suggested one.
- Try to keep UID as it is, because it could be linked inside the dashboard and to avoid duplicates UIDs.
- Finally, press the "Import" button

## Tips on Dashboards

Have in mind that each dashboard may have an "Information" icon (as shown in the following image). If you point on it, you'll have aditional information on the current panel. Try to check it while you are browsing or analyzing your data.

![InfoIcon](./screenshots/help/infoicon.png)
___

## Screenshots

### [Amortization Tracker](./dashboards/AmortizationTracker.json)

This dashboard aims to show the depreciation value of the car over time and its journey.
Depreciating a car by its mileage can be done using various methods. A common approach is to use a depreciation rate per mile or to create a depreciation curve based on data. On the other hand, the depreciation of a car due to age can vary depending on several factors such as the make, model, overall condition of the vehicle, and demand in the market. Here you can put your costs, rates and other variable values to have and idea of the depreciated car value and fuel savings.

![Amortization Tracker](./screenshots/AmortizationTracker.png)

### [Battery Health](https://docs.teslamate.org/docs/screenshots/#battery-health)

This dashboard has been already migrated (given) to the core dashboards of Teslamate and will continue developing directly there with the collaboration of all the enthusiasts in the community. You will find it there with the same name **Battery Health**.

![Battery Health](./screenshots/BatteryHealth.png)

### [Browse Charges](https://docs.teslamate.org/docs/screenshots/#charges)

This dashboard has been already migrated (given) to the core dashboards of Teslamate and will continue developing directly there with the collaboration of all the enthusiasts in the community. You will find it there with the name **Charges**.

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

### [Database Information](https://docs.teslamate.org/docs/screenshots/#database-information)

This dashboard has been already migrated (given) to the core dashboards of Teslamate and will continue developing directly there with the collaboration of all the enthusiasts in the community. You will find it there with the name **Database Information**.

![Database Information](./screenshots/DatabaseInfo.png)

### [DC Charging Curves By Carrier](./dashboards/DCChargingCurvesByCarrier.json)

This dasboard is browse your DC charge sessions by charger carriers.

It's important that you have Geo-Fences added related with the name of the carrier
you have recharged your car, or you may want to edit periodically the **name** field of the **addresses** table, so that it contains its name.

For example, if **Teslamate** geolocates the name as *"Esso Purley Way"* you may modify it to *"Esso Purley Way - IONITY"* or *"IONITY Esso Purley Way"*, then you can filter using the filter textbox **IONITY** to show all the charging curves of all charging sessions at that carrier.

![DC Charging Curves By Carrier](./screenshots/DC_ChargingCurvesByCarrier.png)

### [Incomplete Data](./dashboards/IncompleteData.json)

With this dashboard you may find your incomplete drives or charges that have been interrupted by the connection or any other issue. So you may follow the official guide to fix it.

![Incomplete Data](./screenshots/IncompleteData.png)

### [Range Degradation](./dashboards/RangeDegradation.json)

In this dashboard you may analyze your mileage and the range degradation by a selected period.

So you may have an idea of how much of range is lost as well as if there were any failure in Teslamate logging your data.  

![Range Degradation](./screenshots/RangeDegradation.png)

### [Mileage Stats](./dashboards/MileageStats.json)

With this dashboard you may analyze your mileage and number of drives by year, month, week or day.

The dashboard shows a table with the selected period, time driven, distance, number of drives and efficiency then a bar chart to have a better look for comparison.  

![Mileage Stats](./screenshots/MileageStats.png)

### [Speed Rates](./dashboards/SpeedRates.json)

In this dashboard you can browse the speed rates by segments, based on terrain type: Flat, Uphill or Downhill. This way you can see the average consumtion by speed and its average distance.
Likewise, you can see the Top speeds you reached and how long it lasted.

![Speed Rates](./screenshots/SpeedRates.png)

### [Speed & Temperature](./dashboards/SpeedTemperature.json)

In this dashboard you can browse and analyse the car consumption by temperature in short and long stretches. This way you can see the average consumption depending on the temperature to better understand the efficiency of the car in cold or hot climates.

![Speed Temperature](./screenshots/SpeedTemperature.png)

### [Tracking Drives](./dashboards/TrackingDrives.json)

This dashboard is meant to analyze a drive based on a date you select, then you can pass the pointer over the lines in graph
to see data details and a blue point in the map tranking the route. With this option you can analyze a specific point location in the map,
to see the speed, power, SOC, elevation and if battery heater was on.

Be aware that the drive you select in the dropdown list from the top could be outside the time range of the Timeline graph,
if its the case you have to click on the "Zoom to data" button on the graph in order to update it.

Tip: On Grafana you can press "h" to get a keyboard shortcuts if you want to change the current Zoom out time range or use the mouse to select/change the time range.

![Tracking Drives](./screenshots/TrackingDrives.gif)

### [Usage Stats](./dashboards/UsageStats.json)

This dashboard is a summary of how you use the car over the selected period, by default the current year.

The header shows the distance driven, the number of drives, the time behind the wheel, the energy charged and its cost, together with the saving and the avoided CO₂ estimated against a combustion-engine car.

Below it you have a table with your records, your driving habits (the hour you usually leave and the days you drive the most), the efficiency by outside temperature and by average speed, the distribution and the cost of your charges with the top 10 locations, and a month by month table with the distance, the consumption, the cost per 100 km or 100 mi and the saving compared with a combustion-engine car.

The saving and the avoided CO₂ are rough estimates. They compare the distance you drove with the car you would have used instead, so they are calculated with the consumption and the fuel price you enter in the variables at the top:

- **Fuel units** selects how you want to enter the consumption: **L/100 km**, **MPG (US)** or **MPG (UK)**, and the dashboard converts it internally, so the result is the same whichever you pick.
- **Fuel price / L** is always the price **per litre**, also when the consumption is in MPG.
- **Currency** is only for the display, it sets the symbol of the saving columns.

The avoided CO₂ uses the usual factor for petrol, 2.31 kg per litre, so with a diesel car it is an approximation.

Charges without a recorded cost are valued at the default price per kWh, which is 0 by default so they are left out of the cost. Set that variable if you want them counted.

![Usage Stats](./screenshots/UsageStats.png)

## Contributing

The following dashboards, queries and design are the result of many tests and hours of work.
Feel free to take them for your own personal use.

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

If you are able to contibute or improve this project, please fork the repository and create a pull request. I'll really apreciate any enhancement or suggestion. Don't forget to give the project a star! Thanks again!

### Steps to create a pull request

1. Fork the Project
2. Change to the "develop" Branch (`git checkout develop`)
3. Create your Feature Branch (`git checkout -b feature/NewFeature`)
4. Commit your Changes (`git commit -m 'Add some NewFeature'`)
5. Push to the Branch (`git push origin feature/NewFeature`)
6. Open a Pull Request

### Dashboard file metadata

Two pieces of metadata inside the dashboard JSON files are easy to "fix" by mistake, so this is what is deliberate about them:

- **`schemaVersion` is not unified.** The files declare different values (40, 41, 42). That is the number Grafana uses to know how to migrate a dashboard, and file provisioning upgrades each one on load, so all of them end up with the same internal structure. Normalising them would mean passing every dashboard through a save in Grafana, which rewrites all of them panel by panel and hides the change you actually wanted to make. Grafana rewrites the number anyway the next time the dashboard is saved.
- **`pluginVersion` is unified, and enforced.** It is only metadata that Grafana stamps when a panel is saved, but a stale value is misleading, and it turns a one line change into a diff that looks like it touches every panel. All the panels declare the same version, and the validator fails when one of them drifts away.

The generated fields (`id`, `version`, the `sql` object the query builder leaves behind) also change on their own when a dashboard is saved from Grafana.

### Validating the dashboards before opening a pull request

Hand editing these JSON files is error prone, so the repository ships a validator. Run it
before committing:

```bash
# static checks: JSON, duplicated uids, declared variables, time zone conventions
python3 scripts/validate_dashboards.py --no-sql

# everything above, plus preparing every SQL statement against a real
# TeslaMate database (nothing is executed, the queries are only parsed and planned)
python3 scripts/validate_dashboards.py --docker database
python3 scripts/validate_dashboards.py --dsn postgres://user:pass@host:5432/teslamate
```

The SQL level interpolates the Grafana variables and macros the same way Grafana does,
so it catches the mistakes that would otherwise only show up when a panel is opened:
a renamed or removed column, a bad join, a type error, a variable that is not declared.
It needs a migrated TeslaMate schema, either the container of a local installation
(`--docker`, with `--docker-user` and `--docker-db` if they are not `teslamate`) or any
reachable PostgreSQL instance (`--dsn`). It refuses to run against a database that does
not look like TeslaMate, and it only reads: every statement is prepared inside a
transaction that is rolled back.

The static checks are the ones that run in CI on every pull request
(`.github/workflows/validate-dashboards.yml`), because they need no database. Warnings do
not fail the build; add `--strict` if you want them to.

### Dates and time zones in the queries

Date and time columns in TeslaMate (`start_date`, `end_date`, `date`, ...) are stored as
`timestamp without time zone`, **always in UTC**. That single fact is behind almost every
mistake made when editing these dashboards, because SQL cannot tell what a naive timestamp
means: the same value behaves differently depending on the type it is given.

| Value | Type | Meaning |
| ----- | ---- | ------- |
| As stored in the database | `timestamp` (naive) | A UTC wall clock. **Not** local time |
| After `timezone('UTC', col)` | `timestamptz` | Still the same instant, now unambiguous |
| After one more conversion to the dashboard zone | `timestamp` (naive) | Local wall clock. This is what `date_trunc` and `to_char` want |

So when grouping a stored column by a local period, **convert it from UTC first**: if you pass
the raw column straight to the dashboard time zone, the query silently treats a UTC value as if
it were already local time, and rows near a month, week or day boundary land in the wrong
bucket (up to 1-2 rows per year, which is why it is so easy to miss).

```sql
-- WRONG: treats the UTC value as if it were already local time
date_trunc('month', timezone('$__timezone', start_date), '$__timezone')

-- RIGHT: interpret the column as UTC, then convert to the dashboard time zone
date_trunc('month', timezone('UTC', start_date), '$__timezone')
```

Two more details worth keeping in mind:

- **Always quote `$__timezone`.** Grafana replaces it with the zone name without adding quotes
  (for example `Europe/Madrid`), and `timezone(Europe/Madrid, ...)` is not valid SQL. Write
  `'$__timezone'`, and remember that it may also return plain `utc`.
- **When a value is already local** (the result of a `date_trunc`, or a column already
  converted), do not convert it again. To turn it back into an instant use
  `timezone('$__timezone', local_value)`; this is what the `date_to` columns of the period
  tables do to build the links to other dashboards.

An equivalent and sturdier spelling is `AT TIME ZONE`, which keeps the types explicit and does
not depend on the server session time zone (the `timezone()` function returns a `timestamptz`,
so any naive result derived from it depends on the session). Both work today because the Grafana
container runs in UTC; prefer this one if you are adding new panels:

```sql
-- stored naive UTC -> local naive  (e.g. to group by local month)
date_trunc('month', start_date AT TIME ZONE 'UTC' AT TIME ZONE '$__timezone')

-- local naive -> instant, in milliseconds (e.g. for a data link)
EXTRACT(EPOCH FROM (period AT TIME ZONE '$__timezone')) * 1000
```

Finally, remember that a single query must be consistent whether it groups by local time or by
UTC, and that the pattern around it (`timezone('UTC', timezone('$__timezone', x))` and similar
nested calls) is intentional, not a duplication: each call is a different direction of the
conversion. Before changing one of these expressions, run the old and the new version against
real data and compare the resulting buckets.

Do not take the dashboards much less upload or merge them to other repositories as if the original idea were yours, nor do you share it on social media without mentioning the author. Please, **respect the ingenuity and work of others**. Enjoy!

## Donations

|     |     |
| --- | --- |
| If you like my work and want to support me, buying me a coffee would be greatly appreciated! Your support helps me to keep creating and improving these dashboards. Thank you! | [![Paypal Donate](https://img.shields.io/badge/Donate-PayPal-ff69b4.svg)](https://www.paypal.com/donate/?business=MAWY99TACEXSU&no_recurring=0&currency_code=EUR) |
| Other way to support me is to use [my referral link](https://ts.la/juancarlos32618) to purchase a Tesla product and get Credits you can redeem for exclusive awards like Supercharging miles, merchandise, and accessories. | [![Tesla referral link](./screenshots/help/tesla.png)](https://ts.la/juancarlos32618) |
|     |     |

## Credits

- Author: [Juan Carlos Heredia](https://infoinnova.net/about)
- Based on/forked from [Adrian Kumpf](https://github.com/adriankumpf/teslamate) original code, with improvement of custom Grafana Dashboards (see [contributions history](https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards/graphs/contributors)).

## License

Licensed under the [MIT license][license-url].

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
