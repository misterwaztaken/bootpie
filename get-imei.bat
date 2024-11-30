adb shell "service call iphonesubinfo 1 s16 com.android.shell | cut -d "'" -f2 | grep -Eo '[0-9]' | xargs | sed 's/\ //g'"
