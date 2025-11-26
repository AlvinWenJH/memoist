## Goals
- Add WhisperLiveKit service to `compose.yml`
- Provide easy switching between GPU and CPU builds
- Define logging, network, and volume configuration

## Approach
- Create two services with Compose profiles: `whisperlivekit-gpu` and `whisperlivekit-cpu`
- GPU service builds from `WhisperLiveKit/Dockerfile` and requests NVIDIA GPUs
- CPU service builds from `WhisperLiveKit/Dockerfile.cpu`
- Common settings: port `8000`, named network `wlk-net`, named volume `hf-cache` for HuggingFace cache, JSON-file logging, `restart: unless-stopped`

## Proposed compose.yml
```yaml
version: "3.8"

services:
  whisperlivekit-gpu:
    profiles: ["gpu"]
    build:
      context: ./WhisperLiveKit
      dockerfile: Dockerfile
      args:
        EXTRAS: ""
        HF_PRECACHE_DIR: ""
        HF_TKN_FILE: ""
    device_requests:
      - driver: nvidia
        count: all
        capabilities: ["gpu"]
    ports:
      - "8000:8000"
    networks:
      - wlk-net
    volumes:
      - hf-cache:/root/.cache/huggingface/hub
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    restart: unless-stopped

  whisperlivekit-cpu:
    profiles: ["cpu"]
    build:
      context: ./WhisperLiveKit
      dockerfile: Dockerfile.cpu
      args:
        EXTRAS: ""
        HF_PRECACHE_DIR: ""
        HF_TKN_FILE: ""
    ports:
      - "8000:8000"
    networks:
      - wlk-net
    volumes:
      - hf-cache:/root/.cache/huggingface/hub
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    restart: unless-stopped

networks:
  wlk-net:
    driver: bridge

volumes:
  hf-cache:
```

## Usage
- GPU: `docker compose --profile gpu up --build`
- CPU: `docker compose --profile cpu up --build`

## Notes
- The Dockerfiles already set the entrypoint to `whisperlivekit-server`; the services will expose `http://localhost:8000/`.
- Optional build args can be set in Compose or removed if not needed.
- On Windows, ensure Docker Desktop has NVIDIA GPU support enabled to use the GPU profile.