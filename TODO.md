* Build sub-directories containing scripts
    - Support paths being expressed relatively to each directory's script)
* Proper async jobs
* Optionally produce build manifests, then reload them to determine whether what we're building is different from what exists already at a build location
* Improve tooling surrounding shell commands
    - Store command output and print it all in one go to avoid interleaved output
* Add ArgumentParser:
    * targets
    * -j --jobs
    * --version
    * -q, --quiet
    * -v, -vv, -vvv
    * -k --keep-going: keep building as much as possible even if there's a failure
    * -e --expand-only: do not build, just perform the initial expansion of target nodes. Useful with -vvv.
    * -l --list-targets: expand graph and list all targets
* Unit tests
