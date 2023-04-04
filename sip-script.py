import re
import sys
import subprocess


def parse_file(filename,peers):
    with open(filename,'r') as f:
        last_peer = None
        for line in f:
            if len(line.strip()) == 0 or line.strip()[0] == ';':
                continue
            cur_peer = re.search(r"^\[(\d+)\].*", line.strip())
            if cur_peer is None and last_peer is not None:
                peer_properties = re.search(r"(\w+)=(.+)", line)
                peers[last_peer][peer_properties.group(1)] = peer_properties.group(2)
            else:
                if cur_peer.group(1) in peers:
                    print(f'Duplicate peer: {cur_peer.group(1)}, check your file!')
                    sys.exit(1)
                peers[cur_peer.group(1)]={}
                last_peer = cur_peer.group(1)


def show_peer(peer):
    print(f'\nPeer {peer}')
    if peer in peers:
        for key, value in peers[peer].items():
            print(key, ': ', value, sep='')
    else:
        print('No such peer in users.conf!')
        sys.exit(1)
    #subprocess.run('sudo asterisk -x "sip show peers" | head -1')
    #subprocess.run('sudo asterisk -x "sip show peers" | grep ' + peer)


def change_peer(peer):
    print(f'\nChanging peer {peer}:')
    for key, value in peers[peer].items():
        if key != 'context':
            print(key,': ',value,'\nNew value? (<Enter> to skip)', sep='')
            new_value = input()
            if new_value != '':
                peers[peer][key] = new_value
    if 'context' not in peers[peer] or peers[peer]['context'] == 'default':
        print('Current context is "default". Change to "longdistance"? y/n (<Enter> to skip)', sep='')
        if input() == 'y':
            peers[peer]['context'] = 'longdistance'
    else:
        print('Current context is "longdistance". Change to "default"? y/n (<Enter> to skip)', sep='')
        if input() == 'y':
            peers[peer]['context'] = 'default'
    if confirm_changes(peer):
        write_file(filename_out)


def add_peer(peer):
    print(f'\nAdding new peer: {peer}')
    if peer in peers:
        print('Peer already existsts!')
        sys.exit(1)
    if peer.isdigit() and len(peer) == 3:
        peers[peer] = {}
    else:
        print('Phone must be 3 digits long')
        sys.exit(1)
    print('\nSecret? (8 characters min)')
    secret = input()
    if len(secret) >= 8:
        peers[peer]['secret'] = secret
    else:
        print('Secret must be at least 8 characters long')
        sys.exit(1)

    parse_groups(peers, peer_groups)
    print('\nCurrent groups:')
    for key in peer_groups.keys():
        print(key, end='\t')
    print('\nGroup name? (<Enter> to skip)')
    group = input()
    if group != '':
        peers[peer]['namedcallgroup'] = group
        peers[peer]['namedpickupgroup'] = group

    print('\nCurrent context is "default". Change to "longdistance"? y/n (<Enter> to skip)', sep='')
    if input() == 'y':
        peers[peer]['context'] = 'longdistance'

    if confirm_changes(peer):
        write_file(filename_out)


def remove_peer(peer):
    print('\n!!!   Removing peer:   !!!')
    if peer not in peers:
        print('No such peer!')
        sys.exit(1)
    if confirm_changes(peer):
        del peers[peer]
        write_file(filename_out)


def parse_groups(peers, peer_groups):
    for peer in peers:
        if 'namedcallgroup' in peers[peer] and 'namedpickupgroup' in peers[peer]:
            if peers[peer]['namedcallgroup'] != peers[peer]['namedpickupgroup']:
                print(f'Peer groups mismatch, peer: {peer}, check your file!')
                sys.exit(1)
            if peers[peer]['namedcallgroup'] not in peer_groups:
                peer_groups[peers[peer]['namedcallgroup']] = []
            peer_groups[peers[peer]['namedcallgroup']].append(peer)


def show_groups(peers, peer_groups):
    parse_groups(peers, peer_groups)
    for group, peers in peer_groups.items():
        print('\n', group,':', end='\t', sep='')
        for peer in peers:
            print(peer, end='\t', sep='')


def set_group():
    print('Enter group name:')
    group_name = input()
    if group_name == '':
        print('Group not specified!')
        sys.exit(1)
    print('Enter phones for this group, separated with spaces:')
    peer_list = input().split()
    if len(peer_list) == 0:
        print('Phones not specified!')
        sys.exit(1)
    for peer in peer_list:
        if peer not in peers:
            print(f'No such peer: {peer}!')
            sys.exit(1)
        peers[peer]['namedcallgroup'] = group_name
        peers[peer]['namedpickupgroup'] = group_name
    if confirm_changes(peer, display_peer=False):
        write_file(filename_out)


def confirm_changes(peer, display_peer=True):
    if display_peer:
        show_peer(peer)
    print('\nConfirm changes? y/n')
    if input() == 'y':
        return True
    print('Nothing changed. Exiting')
    sys.exit(1)


def write_file(filename_out):
    #backup file!
    with open(filename_out, 'w') as f:
        for peer in peers:
            f.write(str('['+peer+'](default)'+'\n'))
            for key,value in peers[peer].items():
                #f.write(str(key+'='+value+'\n'))
                f.write(f'{key}={value}\n')
            f.write('\n')
    print('file updated')
    # shell_cmd = subprocess.run('sudo asterisk -x "sip reload"')
    # if shell_cmd.returncode == 0:
    #     print('sip reloaded')
    # else:
    #     print('sip reload failed!')
    #     sys.exit(1)


if __name__ == '__main__':
    usage = 'This script is used for managing Asterisk sip peers\n' \
            'by editing "/etc/asterisk/asterisco/users.conf" file.\n' \
            'Backup of the old file is saved under the "backup" subdir.\n' \
            '\nUsage:\n' \
            'sip-script.py show | add | change | remove <peer> \t - does an action for a given peer\n' \
            'sip-script.py groups \t - shows current callgroups (*8) and their members\n' \
            'sip-script.py setgroup \t - sets a callgroup for a list of given (existing) peers\n'

    if len(sys.argv) == 1 or sys.argv[1] not in ['show', 'add', 'change', 'remove', 'groups', 'setgroup']:
        print(usage)
        sys.exit(1)
    if sys.argv[1] in ['show', 'add', 'change', 'remove'] and len(sys.argv) != 3:
        print(usage)
        sys.exit(1)
    if sys.argv[1] in ['-h', '--help', 'help']:
        print(usage)
        sys.exit(0)

    filename = 'C:\\AsterNEW\\users_upd.conf'
    filename_out = 'C:\\AsterNEW\\users_upd.conf'
    peers = {}
    peer_groups = {}
    parse_file(filename,peers)

    match (sys.argv[1]):
        case 'show':
            show_peer(sys.argv[2])
        case 'add':
            add_peer(sys.argv[2])
        case 'change':
            change_peer(sys.argv[2])
        case 'remove':
            remove_peer(sys.argv[2])
        case 'groups':
            show_groups(peers, peer_groups)
        case 'setgroup':
            set_group()
