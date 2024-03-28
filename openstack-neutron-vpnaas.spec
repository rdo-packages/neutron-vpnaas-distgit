%global milestone .0rc2
%{!?sources_gpg: %{!?dlrn:%global sources_gpg 1} }
%global sources_gpg_sign 0x2ef3fe0ec2b075ab7458b5f8b702b20b13df2318
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
# we are excluding some BRs from automatic generator
%global excluded_brs doc8 bandit pre-commit hacking flake8-import-order bashate sphinx openstackdocstheme
%global modulename neutron_vpnaas
%global servicename neutron-vpnaas
%global type VPNaaS
%global common_desc This is a %{type} service plugin for Openstack Neutron (Networking) service.

Name:           openstack-%{servicename}
Version:        24.0.0
Release:        0.2%{?milestone}%{?dist}
Epoch:          1
Summary:        Openstack Networking %{type} plugin

License:        Apache-2.0
URL:            http://launchpad.net/neutron/
Source0:        https://tarballs.openstack.org/%{servicename}/%{servicename}-%{upstream_version}.tar.gz
# patches_base=24.0.0.0rc2

# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
Source101:        https://tarballs.openstack.org/%{servicename}/%{servicename}-%{upstream_version}.tar.gz.asc
Source102:        https://releases.openstack.org/_static/%{sources_gpg_sign}.txt
%endif
Source103:        neutron-vpnaas-ovn-vpn-agent.service

Obsoletes:      openstack-neutron-vpn-agent < %{version}
Provides:       openstack-neutron-vpn-agent = %{epoch}:%{version}-%{release}

BuildArch:      noarch

# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
BuildRequires:  /usr/bin/gpgv2
%endif
BuildRequires:  gawk
BuildRequires:  openstack-macros
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  systemd
BuildRequires:	git-core

Requires:       python3-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       openstack-neutron >= %{epoch}:17.0.0

%description
%{common_desc}

%package -n python3-%{servicename}
Summary:        Neutron %{type} Python libraries
Requires:       python3-neutron >= %{epoch}:17.0.0

%description -n python3-%{servicename}
%{common_desc}

This package contains the Neutron %{type} Python library.


%package -n python3-%{servicename}-tests
Summary:        Neutron %{type} tests

Requires:       python3-neutron-tests
Requires:       python3-%{servicename} = %{epoch}:%{version}-%{release}

%description -n python3-%{servicename}-tests
%{common_desc}

This package contains Neutron %{type} test files.


%package -n openstack-%{servicename}-ovn-vpn-agent
Summary:        VPNaaS support for OVN

Requires:       python3-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       openstack-neutron-common

%description -n openstack-%{servicename}-ovn-vpn-agent
%{common_desc}

This package contains stand-alone VPN agent to support OVN+VPN.


%prep
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
%{gpgverify}  --keyring=%{SOURCE102} --signature=%{SOURCE101} --data=%{SOURCE0}
%endif
%autosetup -n %{servicename}-%{upstream_version} -S git


sed -i /^[[:space:]]*-c{env:.*_CONSTRAINTS_FILE.*/d tox.ini
sed -i "s/^deps = -c{env:.*_CONSTRAINTS_FILE.*/deps =/" tox.ini
sed -i /^minversion.*/d tox.ini
sed -i /^requires.*virtualenv.*/d tox.ini

# Exclude some bad-known BRs
for pkg in %{excluded_brs}; do
  for reqfile in doc/requirements.txt test-requirements.txt; do
    if [ -f $reqfile ]; then
      sed -i /^${pkg}.*/d $reqfile
    fi
  done
done

%generate_buildrequires
%pyproject_buildrequires -t -e %{default_toxenv}

%build
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%pyproject_wheel

%install
%pyproject_install

# Generate configuration files
export PYTHONPATH="%{buildroot}/%{python3_sitelib}"
for file in `ls etc/oslo-config-generator/*`; do
    oslo-config-generator --config-file=$file
done

find etc -name *.sample | while read filename
do
    filedir=$(dirname $filename)
    file=$(basename $filename .sample)
    mv ${filename} ${filedir}/${file}
done
# Clean wrong automatic config defaults based on buildroot install location

sed -i 's/#ipsec_config_template =.*/#ipsec_config_template =/g' etc/vpn_agent.ini
sed -i 's/#strongswan_config_template =.*/#strongswan_config_template =/g' etc/vpn_agent.ini
sed -i 's/#ipsec_secret_template =.*/#ipsec_secret_template =/g' etc/vpn_agent.ini

sed -i 's/#ipsec_config_template =.*/#ipsec_config_template =/g' etc/neutron_ovn_vpn_agent.ini
sed -i 's/#strongswan_config_template =.*/#strongswan_config_template =/g' etc/neutron_ovn_vpn_agent.ini
sed -i 's/#ipsec_secret_template =.*/#ipsec_secret_template =/g' etc/neutron_ovn_vpn_agent.ini

# Move rootwrap files to proper location
install -d -m 755 %{buildroot}%{_datarootdir}/neutron/rootwrap
mv %{buildroot}/usr/etc/neutron/rootwrap.d/*.filters %{buildroot}%{_datarootdir}/neutron/rootwrap

# Move config files to proper location
install -d -m 755 %{buildroot}%{_sysconfdir}/neutron
mv etc/*.ini etc/*.conf %{buildroot}%{_sysconfdir}/neutron

# Create and populate distribution configuration directory for VPN agent
# (the same as for L3 agent)
mkdir -p %{buildroot}%{_datadir}/neutron/l3_agent
ln -s %{_sysconfdir}/neutron/vpn_agent.ini %{buildroot}%{_datadir}/neutron/l3_agent/vpn_agent.conf

# Create configuration directory that can be populated by users with custom *.conf files
mkdir -p %{buildroot}/%{_sysconfdir}/neutron/conf.d/neutron-vpn-agent

# Make sure neutron-server loads new configuration file
mkdir -p %{buildroot}/%{_datadir}/neutron/server
ln -s %{_sysconfdir}/neutron/%{modulename}.conf %{buildroot}%{_datadir}/neutron/server/%{modulename}.conf

install -p -D -m 644 %{SOURCE103} %{buildroot}%{_unitdir}/neutron-vpnaas-ovn-vpn-agent.service


%post -n openstack-%{servicename}-ovn-vpn-agent
%systemd_post neutron-vpnaas-ovn-vpn-agent.service


%preun -n openstack-%{servicename}-ovn-vpn-agent
%systemd_preun neutron-vpnaas-ovn-vpn-agent.service


%postun -n openstack-%{servicename}-ovn-vpn-agent
%systemd_postun_with_restart neutron-vpnaas-ovn-vpn-agent

%files
%license LICENSE
%doc AUTHORS CONTRIBUTING.rst README.rst
%{_bindir}/neutron-vpn-netns-wrapper
%{_datarootdir}/neutron/rootwrap/vpnaas.filters
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/vpn_agent.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/%{modulename}.conf
%dir %{_sysconfdir}/neutron/conf.d
%dir %{_sysconfdir}/neutron/conf.d/neutron-vpn-agent
%{_datadir}/neutron/l3_agent/*.conf
%{_datadir}/neutron/server/%{modulename}.conf


%files -n python3-%{servicename}
%{python3_sitelib}/%{modulename}
%{python3_sitelib}/%{modulename}*.dist-info
%exclude %{python3_sitelib}/%{modulename}/tests


%files -n python3-%{servicename}-tests
%{python3_sitelib}/%{modulename}/tests


%files -n openstack-%{servicename}-ovn-vpn-agent
%{_bindir}/neutron-ovn-vpn-agent
%{_unitdir}/neutron-vpnaas-ovn-vpn-agent.service
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/neutron_ovn_vpn_agent.ini

%changelog
* Thu Mar 28 2024 RDO <dev@lists.rdoproject.org> 1:24.0.0-0.2.0rc1
- Update to 24.0.0.0rc2

* Mon Mar 18 2024 RDO <dev@lists.rdoproject.org> 1:24.0.0-0.1.0rc1
- Update to 24.0.0.0rc1


