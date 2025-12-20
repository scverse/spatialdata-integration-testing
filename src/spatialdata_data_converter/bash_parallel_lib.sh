run_parallel() {
    local parallel=true
    local cmds=()

    # Parse arguments
    for arg in "$@"; do
        if [[ "$arg" == "--no-parallel" ]]; then
            parallel=false
        else
            cmds+=("$arg")
        fi
    done

    local pids=()
    local fail=0

    if [[ "$parallel" == "false" ]]; then
        # Run commands sequentially for debugging
        echo "Running in serial mode (parallelization disabled)"
        for cmd in "${cmds[@]}"; do
            echo "Executing: $cmd"
            if ! bash -c "$cmd"; then
                echo "Command failed: $cmd"
                exit 1
            fi
        done
    else
        # Run commands in parallel (original behavior)
        for cmd in "${cmds[@]}"; do
            bash -c "$cmd" &
            pids+=($!)
        done

        for pid in "${pids[@]}"; do
            if ! wait $pid; then
                echo "A subprocess failed. Killing all..."
                kill "${pids[@]}" 2>/dev/null || true
                exit 1
            fi
        done
    fi
}
