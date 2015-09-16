__author__ = 'davidkavanagh'
import sys
import json


if __name__=='__main__':

    nodes = []
    edges = []

    with open(sys.argv[1]) as network_file:
        header = network_file.next().rstrip().rsplit()

        for line in network_file:
            fields = line.rstrip().rsplit()
            data = dict(zip(header, fields))
            nA = data['nodeA']
            nB = data['nodeB']

            #will make into set after loop, to get rid of duplicate nodes
            nodes.append(nA)
            nodes.append(nB)

            # data: { id: 'e1', source: 'n1', target: 'n2' } }
            edge_id = 'e.{0}-{1}'.format(nA, nB)
            edge = {'data': {'id': edge_id, 'source': nA, 'target': nB}}
            del data['nodeA']
            del data['nodeB']

            edges.append(edge)

    nodes = set(nodes)

    elements = {'nodes':[], 'edges':[]}
    for n in nodes:
        d = {'data': {'id': n}}
        print d
        elements['nodes'].append(d)

    for e in edges:
        print e
        elements['edges'].append(e)












