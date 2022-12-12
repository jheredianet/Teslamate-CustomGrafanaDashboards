# TeslaMate Custom Grafana Dashboards

This is a repository with custom **Grafana Dashboards**, created especially to work with a Teslamate installation.

## TeslaMate

**[Teslamate](https://docs.teslamate.org/)** is a powerful, self-hosted data logger for your Tesla.

- Written in **[Elixir](https://elixir-lang.org/)**
- Data is stored in a **Postgres** database
- Visualization and data analysis with **Grafana**
- Vehicle data is published to a local **MQTT** Broker

## How to import these custom boards

1. On Grafana (from Teslamate instance), Browse Dashboards then Import...
2. Upload JSON file or import via panel json by pasting the raw content of te JSON file.
3. On the next screen you may name the dashboard as you wish or accept the suggested one.
4. Try to keep UID as it is, because it could be linked inside the dashboard and to avoid duplicates UIDs.
5. Then select the appropiate Teslamate datasource from the available droplist.
6. Finally, press the "Import" button

## Screenshots

### [Current Drive View](./dashboards/CurrentDriveView.json)

This is a special dashboar to load while driving. When you open this dashboard it will show the last 15 minutes, but you should click the "Current Drive" button at the top right corner, to enter in Kiosk mode:

- If you are driving, you will see the information from the time the current drive started till now and it will refesh automatically every 30 seconds.
- If you are just browsing (not driving) you will see the information of the last drive.  

![Current Drive View](./screenshots/CurrentDriveView.png)

## Contributing

If you are able to contibute with more Custom Grafana Dashboards just fork this repository and make a pull request. I'll really apreciate any improvement or suggestion.

## Credits

- Author: [Juan Carlos Heredia](https://infoinnova.net/contacto/)
- Based on/forked from [Adrian Kumpf](https://github.com/adriankumpf/teslamate) original code, with improvement of custom Grafana Dashboards (see [contributions history](https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards/graphs/contributors)).

## License

Licensed under the [MIT license](./LICENSE).
