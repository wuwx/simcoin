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
        node.connect([str(node.ip) for node in nodes[max(0, i - 5):i]])
        wait_until_height_reached(node, i * config.start_blocks_per_node)
        node.generate_block(config.start_blocks_per_node)

    wait_until_height_reached(nodes[0], len(nodes))
    nodes[0].generate_block(config.warmup_blocks)

    for node in nodes:
        wait_until_height_reached(node, config.warmup_blocks + config.start_blocks_per_node * len(nodes))

    delete_nodes(nodes)

    logging.info('End of warmup')


def delete_nodes(nodes):
    for node in nodes:
        node.delete_peers_file()
        node.stop()
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
    while int(node.get_block_count()) < height:
        logging.debug('Waiting until height={} is reached...'.format(str(height)))
        utils.sleep(0.2)