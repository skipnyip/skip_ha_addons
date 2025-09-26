#!/usr/bin/bashio

CONFIG_PATH=/data/options.json

MQTT_HOST="$(bashio::config 'mqtt_host')"
MQTT_PORT="$(bashio::config 'mqtt_port')"
MQTT_USERNAME="$(bashio::config 'mqtt_user')"
MQTT_PASSWORD="$(bashio::config 'mqtt_password')"
MQTT_TOPIC="$(bashio::config 'mqtt_topic')"
MQTT_RETAIN="$(bashio::config 'mqtt_retain')"
PROTOCOL="$(bashio::config 'protocol')"
UNITS="$(bashio::config 'units')"
DISCOVERY_PREFIX="$(bashio::config 'discovery_prefix')"
DISCOVERY_INTERVAL="$(bashio::config 'discovery_interval')"
WHITELIST_ENABLE="$(bashio::config 'whitelist_enable')"
WHITELIST="$(bashio::config 'whitelist')"
AUTO_DISCOVERY="$(bashio::config 'auto_discovery')"
DEBUG="$(bashio::config 'debug')"
EXPIRE_AFTER="$(bashio::config 'expire_after')"

export LANG=C
PATH="/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"
export LD_LIBRARY_PATH=/usr/local/lib64

bashio::log.blue "::::::::Starting RTL_433 with parameters::::::::"
bashio::log.info "MQTT Host =" $MQTT_HOST
bashio::log.info "MQTT port =" $MQTT_PORT
bashio::log.info "MQTT User =" $MQTT_USERNAME
# ... (other info logs can remain here) ...

# Start the Home Assistant discovery script in the background.
# Its only job is to listen to MQTT messages. The '&' runs it in the background.
bashio::log.info "Starting the MQTT to Home Assistant discovery script..."
/usr/bin/python3 /scripts/rtl_433_mqtt_hass.py &

# Give the python script a moment to initialize
sleep 5

# Start and manage the rtl_433 process in a resilient watchdog loop.
while true; do
    bashio::log.info "Starting rtl_433 process..."

    # We pipe rtl_433's console output to a 'while read' loop.
    # The 'read -t 120' will time out if no new console lines are printed
    # by rtl_433 within 120 seconds, which happens when it freezes.
    /usr/bin/rtl_433 $PROTOCOL -C $UNITS -F mqtt://$MQTT_HOST:$MQTT_PORT,user=$MQTT_USERNAME,pass=$MQTT_PASSWORD,retain=$MQTT_RETAIN,events=$MQTT_TOPIC/events,states=$MQTT_TOPIC/states,devices=$MQTT_TOPIC[/model][/id][/channel:A] -M time:tz:local -M protocol -M level | while IFS= read -t 120 -r line; do
        # This loop's only purpose is to detect a timeout.
        # We can log the direct output from rtl_433 here for debugging if needed.
        if [[ "$DEBUG" == "true" ]]; then
            bashio::log.debug "rtl_433 raw output: $line"
        fi
    done

    # If the pipe breaks (due to timeout or rtl_433 crashing), this code will run.
    bashio::log.warning "rtl_433 process timed out or exited. Restarting in 10 seconds..."
    sleep 10
done
