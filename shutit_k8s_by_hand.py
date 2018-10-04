# Generated by shutit skeleton
import random
import datetime
import logging
import string
import os
import inspect
from shutit_module import ShutItModule

class shutit_k8s_by_hand(ShutItModule):


	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		shutit.build['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
		shutit.build['module_name'] = 'shutit_k8s_by_hand_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.build['this_vagrant_run_dir'] = shutit.build['vagrant_run_dir'] + '/' + shutit.build['module_name']
		shutit.send(' command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])
		shutit.send('command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(shutit.build['this_vagrant_run_dir'] + '/Vagrantfile','''Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end

  config.vm.define "k8sbyhand1" do |k8sbyhand1|
    k8sbyhand1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    k8sbyhand1.vm.hostname = "k8sbyhand1.vagrant.test"
    config.vm.provider :virtualbox do |vb|
      vb.name = "shutit_k8s_by_hand_1"
    end
  end
  config.vm.define "k8sbyhand2" do |k8sbyhand2|
    k8sbyhand2.vm.box = ''' + '"' + vagrant_image + '"' + '''
    k8sbyhand2.vm.hostname = "k8sbyhand2.vagrant.test"
    config.vm.provider :virtualbox do |vb|
      vb.name = "shutit_k8s_by_hand_2"
    end
  end
  config.vm.define "k8sbyhand3" do |k8sbyhand3|
    k8sbyhand3.vm.box = ''' + '"' + vagrant_image + '"' + '''
    k8sbyhand3.vm.hostname = "k8sbyhand3.vagrant.test"
    config.vm.provider :virtualbox do |vb|
      vb.name = "shutit_k8s_by_hand_3"
    end
  end
end''')

		# machines is a dict of dicts containing information about each machine for you to use.
		machines = {}
		machines.update({'k8sbyhand1':{'fqdn':'k8sbyhand1.vagrant.test'}})
		machines.update({'k8sbyhand2':{'fqdn':'k8sbyhand2.vagrant.test'}})
		machines.update({'k8sbyhand3':{'fqdn':'k8sbyhand3.vagrant.test'}})

		try:
			pw = open('secret').read().strip()
		except IOError:
			pw = ''
		if pw == '':
			shutit.log("""You can get round this manual step by creating a 'secret' with your password: 'touch secret && chmod 700 secret'""",level=logging.CRITICAL)
			pw = shutit.get_env_pass()
			import time
			time.sleep(10)

		# Set up the sessions
		shutit_sessions = {}
		for machine in sorted(machines.keys()):
			shutit_sessions.update({machine:shutit.create_session('bash')})
		# Set up and validate landrush
		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			shutit_session.send('cd ' + shutit.build['this_vagrant_run_dir'])
			# Remove any existing landrush entry.
			shutit_session.send('vagrant landrush rm ' + machines[machine]['fqdn'])
			# Needs to be done serially for stability reasons.
			try:
				shutit_session.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + machine_name,{'assword for':pw,'assword:':pw})
			except NameError:
				shutit.multisend('vagrant up ' + machine,{'assword for':pw,'assword:':pw},timeout=99999)
			if shutit.send_and_get_output("vagrant status 2> /dev/null | grep -w ^" + machine + " | awk '{print $2}'") != 'running':
				shutit.pause_point("machine: " + machine + " appears not to have come up cleanly")
			ip = shutit.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''')
			machines.get(machine).update({'ip':ip})
			shutit_session.login(command='vagrant ssh ' + machine)
			shutit_session.login(command='sudo su - ')
			# Correct /etc/hosts
			shutit_session.send(r'''cat <(echo $(ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/') $(hostname)) <(cat /etc/hosts | grep -v $(hostname -s)) > /tmp/hosts && mv -f /tmp/hosts /etc/hosts''')
			# Correct any broken ip addresses.
			if shutit.send_and_get_output('''vagrant landrush ls | grep ''' + machine + ''' | grep 10.0.2.15 | wc -l''') != '0':
				shutit_session.log('A 10.0.2.15 landrush ip was detected for machine: ' + machine + ', correcting.',level=logging.WARNING)
				# This beaut gets all the eth0 addresses from the machine and picks the first one that it not 10.0.2.15.
				while True:
					ipaddr = shutit_session.send_and_get_output(r'''ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/' ''')
					if ipaddr[0] not in ('1','2','3','4','5','6','7','8','9'):
						time.sleep(10)
					else:
						break
				# Send this on the host (shutit, not shutit_session)
				shutit.send('vagrant landrush set ' + machines[machine]['fqdn'] + ' ' + ipaddr)
			# Check that the landrush entry is there.
			shutit.send('vagrant landrush ls | grep -w ' + machines[machine]['fqdn'])
		# Gather landrush info
		for machine in sorted(machines.keys()):
			ip = shutit.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''')
			machines.get(machine).update({'ip':ip})

		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			shutit_session.run_script(r'''#!/bin/sh
# See https://raw.githubusercontent.com/ianmiell/vagrant-swapfile/master/vagrant-swapfile.sh
fallocate -l ''' + shutit.cfg[self.module_id]['swapsize'] + r''' /swapfile
ls -lh /swapfile
chown root:root /swapfile
chmod 0600 /swapfile
ls -lh /swapfile
mkswap /swapfile
swapon /swapfile
swapon -s
grep -i --color swap /proc/meminfo
echo "
/swapfile none            swap    sw              0       0" >> /etc/fstab''')
			shutit_session.multisend('adduser person',{'Enter new UNIX password':'person','Retype new UNIX password:':'person','Full Name':'','Phone':'','Room':'','Other':'','Is the information correct':'Y'})

		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			shutit_session.install('python')
			shutit_session.send('''cat <<- EOF >> /etc/network/interfaces
auto ens7
iface ens7 inet static
    address ''' + machines[machine]['ip'] + '''
    netmask 255.255.0.0
    mtu 1450
EOF''')
			shutit_session.send('ifup ens7')
			shutit_session.install('apt-transport-https')
			shutit_session.install('docker.io')
			shutit_session.send('systemctl start docker')
			shutit_session.send('systemctl enable docker')
			shutit_session.send('curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add')
			shutit_session.send('echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" >/etc/apt/sources.list.d/kubernetes.list')
			shutit_session.install('kubelet')
			shutit_session.install('kubeadm')
			shutit_session.install('kubectl')
			shutit_session.install('kubernetes-cni')
			shutit_session.install('nfs-common')
			shutit_session.send('(sleep 10 && reboot) &')
			shutit_session.logout()
			shutit_session.logout()
		time.sleep(60)
		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			shutit_session.login(command='vagrant ssh ' + machine)
			shutit_session.login(command='sudo su - ')

		shutit_session_1 = shutit_sessions['k8sbyhand1']
		shutit_session_1.send('kubeadm init --allocate-node-cidrs=true --cluster-cidr=10.244.0.0/16')
		shutit_session_1.send('mkdir -p $HOME/.kube')
		shutit_session_1.send('cp -i /etc/kubernetes/admin.conf $HOME/.kube/config')
		shutit_session_1.send('chown $(id -u):$(id -g) $HOME/.kube/config')
		shutit_session_1.pause_point('')
		return True


	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/xenial64')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='1024')
		shutit.get_config(self.module_id,'swapsize',default='2G')
		return True

	def test(self, shutit):
		return True

	def finalize(self, shutit):
		return True

	def is_installed(self, shutit):
		return False

	def start(self, shutit):
		return True

	def stop(self, shutit):
		return True

def module():
	return shutit_k8s_by_hand(
		'git.shutit_k8s_by_hand.shutit_k8s_by_hand', 759375484.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)
