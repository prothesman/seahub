# Copyright (c) 2012-2016 Seafile Ltd.
# encoding: utf-8

import json
import logging

from django.core.management.base import BaseCommand

from seaserv import seafile_api

from seahub.alibaba.models import MessageQueue, Profile

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Read messages from alibaba message queue database table."

    def handle(self, *args, **options):

        self.stdout.write("Start.\n")
        messages = MessageQueue.objects.filter(is_consumed=0)

        for message in messages:

            if message.topic == '00-leave_file_handover':

                message_dict = json.loads(message.message_body)
                leave_work_no = message_dict['leaveWorkNo']
                super_work_no = message_dict['superWorkNo']
                leave_work_profile = Profile.objects.get_profile_by_work_no(leave_work_no)
                super_work_profile = Profile.objects.get_profile_by_work_no(super_work_no)

                if leave_work_profile and super_work_profile:

                    leave_ccnet_email = leave_work_profile.uid
                    super_ccnet_email = super_work_profile.uid
                    leave_owned_repos = seafile_api.get_owned_repo_list(
                            leave_ccnet_email, ret_corrupted=False)

                    for repo in leave_owned_repos:
                        if seafile_api.repo_has_been_shared(repo.id, including_groups=True):
                            seafile_api.set_repo_owner(repo.id, super_ccnet_email)
                        else:
                            seafile_api.remove_repo(repo.id)

        self.stdout.write('Done.\n')
