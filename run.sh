# Build Image
echo "Building image..."
docker build -t egu_net .

# Run Container
echo "Running container..."
docker run \
  -it --rm \
  --name egu-net \
  -u $(id -u):$(id -g) \
  -v $PWD:/tf \
  egu_net \
  bash
