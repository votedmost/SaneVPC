#!/usr/bin/env python
""" SaneVPC : boto VPC :: requests : urllib """

import itertools
import boto
from boto import ec2, vpc

def get_vpc_by_name(name):
    # TODO - take conn or region kwarg
    conn = boto.vpc.connect_to_region("us-west-2")
    vpcs = [ vpc for vpc in conn.get_all_vpcs() if \
             vpc.tags.get("Name","") == name ]
    if not len(vpcs):
        raise Exception("No VPC named %s found" % name)
    if len(vpcs) > 1:
        raise Exception("Multiple VPCs named %s found" % name )
    vpc = vpcs[0]
    SaneVPC.upgrade_from_boto_vpc(vpc)
    return vpc

class SaneVPC(boto.vpc.vpc.VPC):
    # update() is for polling - should we create
    # wait_for_condition(attr,value,callback,timeout=N)?
    def __init__(self, *args, **kwargs):
        super(SaneVPC,self).__init__(*args, **kwargs)
        self._upgrade_thyself()

    def _upgrade_thyself(self):
        self.instances = []
        self.subnets = []
        self.security_groups = {}

    @classmethod
    def upgrade_from_boto_vpc(cls, vpc):
        # should this deepcopy vpc instance, upgrade it, and return it?
        vpc.__class__ = cls
        vpc._upgrade_thyself()

    def update_instances(self):
        res = self.connection.get_all_instances(filters={"vpc-id":self.id})
        self.instances = list(itertools.chain(*[r.instances for r in res]))
        # TODO - make dict by tags['Name']

    def update_subnets(self):
        filters={"vpcId":self.id}
        self.subnets = self.connection.get_all_subnets(filters=filters)

    def update_security_groups(self):
        filters ={"vpc-id":self.id}
        groups = self.connection.get_all_security_groups(filters=filters)
        # TODO - are group names necessarily unique within a VPC?
        self.security_groups = { group.name: group for group in groups }

    def deep_update(self):
        """Goes through all children (security groups, instances, etc) and 
           runs deep_refresh on them.
        """
        raise NotImplementedError

    def update(self):
        self.update_instances()
        self.update_security_groups()
        self.update_subnets()
        super(type(self),self).update()

    def __repr__(self):
        return "<SaneVPC:%s>" % self.id

class SaneSecurityGroup(boto.ec2.securitygroup.SecurityGroup):
    def __init__(self):
        raise NotImplementedError

class SaneSubnet(object):
    # this should clean up rules syntax a bit and also populate self.instances
    # with all instances in subnet
    def __init__(self):
        raise NotImplementedError
