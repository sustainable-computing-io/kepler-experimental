Vagrant.configure("2") do |config|

  # search : https://portal.cloud.hashicorp.com/vagrant/discover?providers=libvirt&query=40-cloud
  #
  config.vm.box = "fedora/40-cloud-base"
  config.vm.box_version = "40.20240414.0"
  config.vm.disk :disk, size: "40GB", primary: true


  # config.vm.network "public_network", ip: "192.168.111.222", dev: "virbr0"
  # config.vm.network :private_network, ip: "192.168.111.222"

  config.vm.provider :libvirt do |domain|
    domain.title = "f40"

    domain.driver = "kvm"
    domain.memory = 2048
    domain.disk_bus = "virtio"    # Use virtio for better performance

    domain.cpu_mode = "host-passthrough"
    domain.cpus = 2
    domain.cpuaffinitiy 0 => '4', 1 => '5'
    domain.cputopology sockets: '1', cores: '2', threads: '1'

    domain.machine_virtual_size = 40
  end

  config.vm.hostname = "vm.kepler.dev"

  config.vm.synced_folder "./vm/dev", "/vagrant",
    type: "rsync",
    rsync__auto: true


  # config.vm.provision "shell", path: "provision.sh"
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "ansible/playbook.yml"
    ansible.verbose = "vv"
  end

end

# commands
# vagrant ssh-config
