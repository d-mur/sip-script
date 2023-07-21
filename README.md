# sip-script
#### This script is used for the Asterisk sip peers management.

`.env` file must contain the following variables:  
`filename` - path to the config file containing asterisk peers
`filename_out` - should be the same as the previous value. can be changed for debugging/testing  
`backup_filename` - path for storing the original file contents (current timestamp will be added automatically)

                                                                                          
#### Usage:  
`sip-script.py show | add | change | remove <peer>` - does the specified action for the given peer  
`sip-script.py groups` - shows current callgroups (*8) and their members  
`sip-script.py setgroup` - sets a callgroup for a list of given (existing) peers
