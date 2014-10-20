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

def get_vpc_by_id(vpcid):
    # TODO - take conn or region kwarg
    # TODO - DRY
    conn = boto.vpc.connect_to_region("us-west-2")
    vpcs = conn.get_all_vpcs(vpc_ids=(vpcid,))
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
        self.instances = {}
        self.subnets = []
        self.security_groups = {}

    @classmethod
    def upgrade_from_boto_vpc(cls, vpc):
        # should this deepcopy vpc instance, upgrade it, and return it?
        vpc.__class__ = cls
        vpc._upgrade_thyself()

    def update_instances(self):
        reservations = self.connection.get_all_instances(filters={"vpc-id":self.id})
        instances ={ instance.tags.get("Name",instance.id): instance for 
                     reservation in reservations for 
                     instance in reservation.instances }
        self.instances = instances

    def update_subnets(self):
        filters={"vpcId":self.id}
        subnets = self.connection.get_all_subnets(filters=filters)
        for subnet in subnets:
            SaneSubnet.upgrade_from_boto_subnet(subnet)
        self.subnets = subnets

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
    # this should clean up rules syntax a bit and also populate self.instances
    # with all instances in subnet
    def __init__(self):
        raise NotImplementedError

class SaneSubnet(boto.vpc.subnet.Subnet):
    def __init__(self, *args, **kwargs):
        super(SaneSubnet,self).__init__(*args, **kwargs)
        self._upgrade_thyself()

    def _upgrade_thyself(self):
        self.vpc = get_vpc_by_id(self.vpc_id)

    @classmethod
    def upgrade_from_boto_subnet(cls, subnet):
        # should this deepcopy vpc instance, upgrade it, and return it?
        subnet.__class__ = cls
        subnet._upgrade_thyself()

    def run_instances(self, *args, **kwargs):
        """
        Runs an image on EC2 within this subnet.

        :type image_id: string
        :param image_id: The ID of the image to run.

        :type min_count: int
        :param min_count: The minimum number of instances to launch.

        :type max_count: int
        :param max_count: The maximum number of instances to launch.

        :type key_name: string
        :param key_name: The name of the key pair with which to
            launch instances.

        :type security_groups: list of strings
        :param security_groups: The names of the EC2 classic security groups
            with which to associate instances

        :type user_data: string
        :param user_data: The Base64-encoded MIME user data to be made
            available to the instance(s) in this reservation.

        :type instance_type: string
        :param instance_type: The type of instance to run:


            * t1.micro
            * m1.small
            * m1.medium
            * m1.large
            * m1.xlarge
            * m3.medium
            * m3.large
            * m3.xlarge
            * m3.2xlarge
            * c1.medium
            * c1.xlarge
            * m2.xlarge
            * m2.2xlarge
            * m2.4xlarge
            * cr1.8xlarge
            * hi1.4xlarge
            * hs1.8xlarge
            * cc1.4xlarge
            * cg1.4xlarge
            * cc2.8xlarge
            * g2.2xlarge
            * c3.large
            * c3.xlarge
            * c3.2xlarge
            * c3.4xlarge
            * c3.8xlarge
            * i2.xlarge
            * i2.2xlarge
            * i2.4xlarge
            * i2.8xlarge

        :type kernel_id: string
        :param kernel_id: The ID of the kernel with which to launch the
            instances.

        :type ramdisk_id: string
        :param ramdisk_id: The ID of the RAM disk with which to launch the
            instances.

        :type monitoring_enabled: bool
        :param monitoring_enabled: Enable CloudWatch monitoring on
            the instance.

        :type private_ip_address: string
        :param private_ip_address: If you're using VPC, you can
            optionally use this parameter to assign the instance a
            specific available IP address from the subnet (e.g.,
            10.0.0.25).

        :type block_device_map: :class:`boto.ec2.blockdevicemapping.BlockDeviceMapping`
        :param block_device_map: A BlockDeviceMapping data structure

        :type disable_api_termination: bool
        :param disable_api_termination: If True, the instances will be locked
            and will not be able to be terminated via the API.

        :type instance_initiated_shutdown_behavior: string
        :param instance_initiated_shutdown_behavior: Specifies whether the
            instance stops or terminates on instance-initiated shutdown.
            Valid values are:

            * stop
            * terminate

        :type placement_group: string
        :param placement_group: If specified, this is the name of the placement
            group in which the instance(s) will be launched.

        :type client_token: string
        :param client_token: Unique, case-sensitive identifier you provide
            to ensure idempotency of the request. Maximum 64 ASCII characters.

        :type security_group_ids: list of strings
        :param security_group_ids: The ID of the VPC security groups with
            which to associate instances.

        :type additional_info: string
        :param additional_info: Specifies additional information to make
            available to the instance(s).

        :type tenancy: string
        :param tenancy: The tenancy of the instance you want to
            launch. An instance with a tenancy of 'dedicated' runs on
            single-tenant hardware and can only be launched into a
            VPC. Valid values are:"default" or "dedicated".
            NOTE: To use dedicated tenancy you MUST specify a VPC
            subnet-ID as well.

        :type instance_profile_arn: string
        :param instance_profile_arn: The Amazon resource name (ARN) of
            the IAM Instance Profile (IIP) to associate with the instances.

        :type instance_profile_name: string
        :param instance_profile_name: The name of
            the IAM Instance Profile (IIP) to associate with the instances.

        :type ebs_optimized: bool
        :param ebs_optimized: Whether the instance is optimized for
            EBS I/O.  This optimization provides dedicated throughput
            to Amazon EBS and an optimized configuration stack to
            provide optimal EBS I/O performance.  This optimization
            isn't available with all instance types.

        :type network_interfaces: list
        :param network_interfaces: A list of
            :class:`boto.ec2.networkinterface.NetworkInterfaceSpecification`

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: Reservation
        :return: The :class:`boto.ec2.instance.Reservation` associated with
                 the request for machines
        """
        kwargs['subnet_id'] = self.id
        return self.connection.run_instances(*args, **kwargs)

    def __repr__(self):
        return "<SaneSubnet:%s>" % self.id
