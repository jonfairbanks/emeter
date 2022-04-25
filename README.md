# emeter
 
Publish Kasa plug metrics to Influx Cloud

![emeter-volts](images/emeter-volts.png)
![emeter-watts](images/emeter-watts.png)
![emeter-milliamps](images/emeter-milliamps.png)

### Setup

- Setup your [Kasa smart plug](https://amzn.to/3JVZXzh) in the Kasa Home app
- Gather the IP address associated with your plug
- [Create a free Influx Cloud account](https://cloud2.influxdata.com/signup)
- Create an Influx Cloud Bucket (power-usage) and API Token

### Usage

The following env variables are **required**:

- INFLUX_TOKEN: API Token provided by Influx Cloud
- INFLUX_ORG: Your Influx Cloud organization name
- INFLUX_BUCKET: Your Influx Cloud bucket name (Default: `power-usage`)
- PLUG: IP Address of the Kasa plug to monitor

Additional supported env variables include:

- DEBUG: Enable or disable in-app debug logging (Default: `False`)
- DEVICE: Preferred name for this device (Default: `My Device`)
- INFLUX_HOST: Host of the Influx Cloud bucket (Default: `https://us-central1-1.gcp.cloud2.influxdata.com`)

### Launch

The application can be launched with `docker-compose`:

```
docker-compose up -d
```

### Dashboard

A sample dashboard is provided in this repo and can be imported:

- Ensure that emeter is running
- Login to Influx Cloud and go to Dashboards
- Use the dropdown on `Create Dashboard` to import the template