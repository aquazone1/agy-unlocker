#!/bin/sh
umask 077
trace_dir="$HOME/.config/antigravity-proxy"
command -v strace >/dev/null || { echo 'strace is not installed'; exit 1; }
trace_workspace=$(mktemp -d /tmp/agy-trace.XXXXXX) || exit 1
cd "$trace_workspace" || exit 1
timeout -k 3s 20s strace -f -qq -tt \
  -e trace=futex,flock,fcntl,connect,openat,wait4,poll,ppoll,epoll_wait,epoll_pwait \
  -o "$trace_dir/trace-syscalls.log" \
  "$HOME/.local/bin/agy-google" \
  --model gemini-3.8-flash-low --disable-slash-commands \
  --log-file "$trace_dir/trace-cli.log" \
  -p 'Не используй инструменты. Ответь только: GOOGLE_OK' \
  >"$trace_dir/trace-stack.log" 2>&1
trace_status=$?
printf 'Exit: %s\n' "$trace_status"
printf 'Trace: %s/trace-syscalls.log\n' "$trace_dir"
printf 'CLI log: %s/trace-cli.log\n' "$trace_dir"
