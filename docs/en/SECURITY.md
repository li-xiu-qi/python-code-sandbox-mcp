# Security Considerations

## Isolation Model

### Docker Containers
The sandbox uses standard Docker containers for isolation. This provides a strong layer of separation from the host system, but it is not a virtualization-level security boundary (like a VM).

- **Filesystem**: The container cannot access the host filesystem unless explicitly mounted. Currently, the server does **not** mount any host directories by default.
- **Network**: Containers are created with default bridge networking. They **do** have internet access (needed for `pip install`), but cannot easily access services running on `localhost` of the host machine without special configuration.

## Resource Limits

To prevent a runaway script from crashing the host machine, the following limits are enforced by default in `docker_utils.py`:

- **Memory**: 2GB (`mem_limit="2g"`)
- **CPU**: 50% of 1 Core (`cpu_period=100000`, `cpu_quota=50000`)
- **Disk**: No explicit quota is enforced by the server code. Containers inherit the default Docker storage limit (typically **20GB** per container on Docker Desktop). Given the ephemeral nature and background cleanup, disk exhaustion is unlikely under normal use.

## Best Practices

1.  **Ephemeral Usage**: Always treat sandboxes as temporary. Do not store critical data inside them.
2.  **Code Injection**: The server uses Base64 encoding to transfer code to the container. This prevents basic shell injection attacks, but malicious Python code running *inside* the container can still attempt to exploit kernel vulnerabilities (though unlikely in recent Docker versions).
3.  **Network Access**: Be aware that code running in the sandbox can make outbound HTTP requests (e.g., `requests.get('http://malicious-site.com')`).

## Future Enhancements
- [ ] Add option to disable network access (network=none).
- [ ] Add configurable timeout for individual code execution (not just container life).
- [ ] Support mounting specific host directories for input/output.

