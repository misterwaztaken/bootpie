> if you haven't realized already bootpie requires root to run on your device
> 
> make sure magisk allows adb to access root or it will not be able to patch
> 
> this requires use of samfirm which will be used to find firmware files for patching

# bootpie

a work-in-progress python utility for processing, editing, compressing and patching (hiding) the unofficial firmware warning for Samsung devices with non-stock operating systems (ROMs and whatnot))

## how it'll work
- bootpie will find the latest firmware version for your device automatically (on a website through a proxy) and also will automatically find up_param in the device's storage.
- it will then proceed with downloading the firmware file to it's asset folder, and unpack it into another folder in the same directory
- it will keep unpacking till it gets to the up_param file, it will unpack that
- finally, it will fill the warning png file all-black, and repack the up_param file and it will flash the up_param file (rewrite technically?) to the device while it's still on 

changes will be visible after restarting

## why

up_param files are hard to dig for manually, specific for your device, and on XDA there's lots of people who don't like this warning. 
this python script aims to eliminate that difficulty by making the process as autonomous and easy as possible, with no hassle.

## when

soon™
