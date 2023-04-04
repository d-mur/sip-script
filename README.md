# sip-script
This script is used for managing Asterisk sip peers                                       
by editing "/etc/asterisk/asterisco/users.conf" file.                                     
Backup of the old file is saved under the "backup" subdir.                                
                                                                                          
Usage:                                                                                    
  sip-script.py show | add | change | remove <peer>        - does an action for a given peer
  
  sip-script.py groups     - shows current callgroups (*8) and their members
  
  sip-script.py setgroup   - sets a callgroup for a list of given (existing) peers
  
