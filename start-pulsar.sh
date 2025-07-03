#!/bin/bash
set -e

# Start Pulsar in the background
echo "🚀 Starting Pulsar..."
bin/pulsar standalone &

# Wait for REST API to be ready, then run setup
echo "🕒 Waiting for Pulsar REST API..."
until curl -sSf http://localhost:8080/admin/v2/clusters > /dev/null; do
  echo "⏳ Pulsar not ready yet..."
  sleep 2
done
echo "✅ Pulsar is ready!"

# Run init script
bash /pulsar/init-pulsar.sh &

# Wait for Pulsar to keep running
wait
