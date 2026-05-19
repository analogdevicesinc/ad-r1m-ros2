#!/usr/bin/env bash

STATUS_LED=/usr/lib/ad-r1m/status-led/status-led.sh

last_status=boot
$STATUS_LED boot &

trap "\"$STATUS_LED\" off; exit" EXIT SIGINT SIGTERM

while true; do
        # Docker service inactive: touch nothing. We are either: running very early, shutting down, breaking down,
        # or the user stopped docker intentionally, for some reason.
        systemctl is-active docker || {
                sleep 0.5
                continue
        }

        # Get list of docker-compose containers and their health statuses
        CONTAINERS=$(docker compose -f /home/analog/compose.yaml ps -q 2>/dev/null)

        # No containers running?
        test -n "${CONTAINERS}" || {
                if [ $last_status != off ]; then
                        last_status=off
                        $STATUS_LED off &
                fi
                sleep 1
                continue
        }

        # Containers running but some not healthy?
        (docker inspect --format "{{json .State.Health.Status }}" $CONTAINERS 2>/dev/null | grep -vq '"healthy"') && {
                if [ $last_status != unhealthy ]; then
                        last_status=unhealthy
                        $STATUS_LED unhealthy &
                fi
                sleep 1
                continue
        }

        if [ $last_status != on ]; then
                last_status=on
                $STATUS_LED on &
        fi
        sleep 1
done