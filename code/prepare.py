import config
import logging
import bash
import dockercmd
import os
import utils


def give_nodes_spendable_coins(nodes):
    logging.info('Begin warmup')

    run_nodes(nodes)

    for i, node in enumerate(nodes):
        for node_to_be_connected in nodes[max(0, i - 5):i]:
            node.execute_rpc('addnode', str(node_to_be_connected.ip), 'add')
        wait_until_height_reached(node, i * config.start_blocks_per_node)
        node.execute_rpc('generate', config.start_blocks_per_node)

    wait_until_height_reached(nodes[0], config.start_blocks_per_node * len(nodes))
    nodes[0].execute_rpc('generate', config.warmup_blocks)

    for node in nodes:
        wait_until_height_reached(node, config.warmup_blocks + config.start_blocks_per_node * len(nodes))

    get_new_second_address(nodes)

    get_coinbase_variables(nodes)

    transfer_coinbase_to_normal_tx(nodes)

    delete_nodes(nodes)

    logging.info('End of warmup')


def get_new_second_address(nodes):
    for node in nodes:
        node.second_address = node.execute_rpc('getnewaddress')


def transfer_coinbase_to_normal_tx(nodes):
    for node in nodes:
        raw_transaction = node.create_coinbase_transfer_tx()
        signed_raw_transaction = node.execute_rpc('signrawtransaction', raw_transaction)['hex']
        node.current_unspent_tx = node.execute_rpc('sendrawtransaction', signed_raw_transaction)


def get_coinbase_variables(nodes):
    for node in nodes:
        unspent_tx = node.execute_rpc('listunspent')[0]

        node.current_unspent_tx = unspent_tx["txid"]
        node.address = unspent_tx["address"]
        node.private_key = node.execute_rpc('dumpprivkey', node.address)


def delete_nodes(nodes):
    for node in nodes:
        node.delete_peers_file()
        node.execute_rpc('stop')
        node.rm()


def run_nodes(nodes):
    for node in nodes:
        node.run()
    utils.sleep(4 + len(nodes) * 0.2)


def prepare_simulation_dir():
    if not os.path.exists(config.sim_dir):
        os.makedirs(config.sim_dir)

    bash.check_output('cp {} {}'.format(config.network_csv, config.sim_dir))
    bash.check_output('cp {} {}'.format(config.ticks_csv, config.sim_dir))

    with open(config.blocks_csv, 'a') as file:
        file.write('node;block;mine_time;stale_block;size;number_of_tx;'
                   'number_of_reached_nodes;propagation_median;propagation_std\n')

    with open(config.tx_csv, 'a') as file:
        file.write('node;tx;number_of_reached_nodes;propagation_median;propagation_std\n')


def remove_old_containers_if_exists():
    containers = bash.check_output(dockercmd.ps_containers())
    if len(containers) > 0:
        bash.check_output(dockercmd.remove_all_containers(), lvl=logging.DEBUG)


def recreate_network():
    exit_code = bash.call_silent(dockercmd.inspect_network())
    if exit_code == 0:
        bash.check_output(dockercmd.rm_network())
    bash.check_output(dockercmd.create_network())


def wait_until_height_reached(node, height):
    while int(node.execute_rpc('getblockcount')) < height:
        logging.debug('Waiting until height={} is reached...'.format(str(height)))
        utils.sleep(0.2)
