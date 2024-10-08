from app.logging import logger


class Chain:
    def __init__(self, name, steps):
        self.name = name
        self.steps = steps

    def __repr__(self):
        return self.name


def generate_chains(chains_dict):
    logger.info(f'Creating chains')
    chains = {
        name: Chain(name, chains_dict[name]) for name in chains_dict.keys()
    }
    return chains
