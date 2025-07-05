bin/pulsar standalone &
PULSAR_PID=$!

# Wait for REST API to be ready
echo "🕒 Waiting for Pulsar REST API..."
until curl -sSf http://localhost:8080/admin/v2/clusters > /dev/null; do
  echo "⏳ Pulsar not ready yet..."
  sleep 2
done
echo "✅ Pulsar is ready!"

# Run init script
bash /pulsar/init-pulsar.sh

# Keep the container running by waiting on Pulsar
wait $PULSAR_PID
