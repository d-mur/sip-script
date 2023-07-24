#!/usr/bin/env python3

import re
import sys
import subprocess
from dotenv import dotenv_values

def parse_file(filename, peers):
    with open(filename, 'r') as f:
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
                    raise SystemExit(f'Duplicate peer: {cur_peer.group(1)}, check your file!')
                peers[cur_peer.group(1)] = {}
                last_peer = cur_peer.group(1)


def show_peer(peer):
    print(f'\nPeer {peer}')
    if peer in peers:
        for key, value in peers[peer].items():
            print(key, ': ', value, sep='')
    else:
        raise SystemExit('No such peer in users.conf!')
    print()
    subprocess.run(r'asterisk -x "sip show peers like" ' + peer, shell=True)
    print()


def change_peer(peer):
    print(f'\nChanging peer {peer}:')
    for key, value in peers[peer].items():
        if key != 'context':
            new_value = input("key,': ',value,'\nNew value? (<Enter> to skip)', sep=''")
            if new_value != '':
                peers[peer][key] = new_value
    if 'context' not in peers[peer] or peers[peer]['context'] == 'default':
        if input('Current context is "default". Change to "longdistance"? y/n (<Enter> to skip)') == 'y':
            peers[peer]['context'] = 'longdistance'
    else:
        if input('Current context is "longdistance". Change to "default"? y/n (<Enter> to skip)') == 'y':
            peers[peer]['context'] = 'default'
    if confirm_changes(peer):
        write_file(filename_out)


def add_peer(peer):
    print(f'\nAdding new peer: {peer}')
    if peer in peers:
        raise SystemExit('Peer already existsts!')
    if peer.isdigit() and len(peer) == 3:
        peers[peer] = {}
    else:
        raise SystemExit('Phone must be 3 digits long')
    secret = input('\nSecret? (8 characters min)')
    if len(secret) >= 8:
        peers[peer]['secret'] = secret
    else:
        raise SystemExit('Secret must be at least 8 characters long')

    parse_groups(peers, peer_groups)
    print('\nCurrent groups:')
    for key in peer_groups.keys():
        print(key, end='\t')
    group = input('\nGroup name? (<Enter> to skip)')
    if group != '':
        peers[peer]['namedcallgroup'] = group
        peers[peer]['namedpickupgroup'] = group

    if input('\nCurrent context is "default". Change to "longdistance"? y/n (<Enter> to skip)') == 'y':
        peers[peer]['context'] = 'longdistance'

    if confirm_changes(peer):
        write_file(filename_out)


def remove_peer(peer):
    print('\n!!!   Removing peer:   !!!')
    if peer not in peers:
        raise SystemExit('No such peer!')
    if confirm_changes(peer):
        del peers[peer]
        write_file(filename_out)


def parse_groups(peers, peer_groups):
    for peer in peers:
        if 'namedcallgroup' in peers[peer] and 'namedpickupgroup' in peers[peer]:
            if peers[peer]['namedcallgroup'] != peers[peer]['namedpickupgroup']:
                raise SystemExit(f'Peer groups mismatch, peer: {peer}, check your file!')
            if peers[peer]['namedcallgroup'] not in peer_groups:
                peer_groups[peers[peer]['namedcallgroup']] = []
            peer_groups[peers[peer]['namedcallgroup']].append(peer)


def show_groups(peers, peer_groups):
    parse_groups(peers, peer_groups)
    for group, peers in peer_groups.items():
        print('\n', group, ':', end='\t', sep='')
        for peer in peers:
            print(peer, end='\t', sep='')
    print('\n')


def set_group():
    group_name = input('Enter group name:')
    if group_name == '':
        raise SystemExit('Group not specified!')
    peer_list = input('Enter phones for this group, separated with spaces:').split()
    if len(peer_list) == 0:
        raise SystemExit('Phones not specified!')
    for peer in peer_list:
        if peer not in peers:
            raise SystemExit(f'No such peer: {peer}!')
        peers[peer]['namedcallgroup'] = group_name
        peers[peer]['namedpickupgroup'] = group_name
    if confirm_changes(peer, display_peer=False):
        write_file(filename_out)


def confirm_changes(peer, display_peer=True):
    if display_peer:
        show_peer(peer)
    if input('\nConfirm changes? y/n') == 'y':
        return True
    raise SystemExit('Nothing changed. Exiting')


def write_file(filename_out):
    backup_cmd = subprocess.run(str('cp ' + filename + ' ' + backup_filename + '.' + '$(date +"%Y%m%d_%H%M%S")'), shell=True)
    if backup_cmd.returncode != 0:
        raise SystemExit('Failed to create backup file!')
    with open(filename_out, 'w') as f:
        for peer in peers:
            f.write(str('[' + peer + '](default)' + '\n'))
            for key, value in peers[peer].items():
                f.write(f'{key}={value}\n')
            f.write('\n')
    print('file updated')
    shell_cmd = subprocess.run('sudo asterisk -x "sip reload"', shell=True)
    if shell_cmd.returncode == 0:
        print('sip reloaded')
    else:
        raise SystemExit('sip reload failed!')


if __name__ == '__main__':
    env = dotenv_values()
    filename = env['filename']
    filename_out = env['filename_out']
    backup_filename = env['backup_filename']

    description = "\nThis script is used for the Asterisk sip peers management.\n \
    .env file must contain the following variables:\n \
    filename  \t \t \t path to the config file containing asterisk peers\n \
    filename_out \t \t should be the same as the previous value. can be changed for debugging/testing\n \
    backup_filename \t path for storing the original file contents (current timestamp will be added automatically)\n"
    usage = "\nUsage:\n \
    sip-script.py show | add | change | remove <peer> \t \t does the specified action for the given peer\n \
    sip-script.py groups \t \t \t \t \t \t \t \t \t shows current callgroups (*8) and their members\n \
    sip-script.py setgroup \t \t \t \t \t \t \t \t sets a callgroup for a list of given (existing) peers\n"

    if len(sys.argv) == 1 or sys.argv[1] not in ['show', 'add', 'change', 'remove', 'groups', 'setgroup']:
        raise SystemExit(description + usage)
    if sys.argv[1] in ['show', 'add', 'change', 'remove'] and len(sys.argv) != 3:
        raise SystemExit(usage)
    if sys.argv[1] in ['-h', '--help', 'help']:
        print(description + usage)
    else:
        peers = {}
        peer_groups = {}
        parse_file(filename, peers)

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
