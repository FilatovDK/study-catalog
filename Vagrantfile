Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "study-catalog-lab7-local"
  config.vm.network "forwarded_port", guest: 8080, host: 8087, host_ip: "127.0.0.1"
  config.vm.provider "virtualbox" do |vb|
    vb.name = "study-catalog-lab7-local"
    vb.memory = 1024
    vb.cpus = 1
  end
  config.vm.provision "shell", inline: "bash /vagrant/deploy-ubuntu.sh local"
end
