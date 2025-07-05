#!/bin/bash
set -e

# Wait until Pulsar REST API is ready
echo "⏳ Waiting for Pulsar REST API..."
until curl -sSf http://localhost:8080/admin/v2/clusters > /dev/null; do
  sleep 2
done
echo "✅ Pulsar is ready."

# Create output topic
echo "📌 Creating output topic 'clean'..."
bin/pulsar-admin topics create persistent://public/default/clean || true

# Deploy validate-cleanse-fn
echo "📦 Deploying validate-cleanse-fn..."

# Remove old function if exists
bin/pulsar-admin functions delete --tenant public --namespace default --name validate-cleanse-fn || true

# Cleanup lingering function metadata
# Cleanup lingering function metadata
rm -rf /pulsar/data/functions/public/default/validate-cleanse-fn
rm -rf /pulsar/functions/public/default/validate-cleanse-fn
rm -rf /pulsar/download/pulsar_functions/public/default/validate-cleanse-fn


# Create function
bin/pulsar-admin functions create \
  --py /pulsar/validate.py \
  --classname validate.Validator \
  --tenant public \
  --namespace default \
  --name validate-cleanse-fn \
  --inputs persistent://public/default/raw-ingest \
  --output persistent://public/default/clean \
  --parallelism 1

echo "✅ validate-cleanse-fn created."
