%global release_name kilo
%global modulename neutron_vpnaas
%global servicename neutron-vpnaas
%global type VPNaaS

%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

Name:           openstack-%{servicename}
Version:        2015.1.3
Release:        1%{?dist}
Summary:        Openstack Networking %{type} plugin

License:        ASL 2.0
URL:            http://launchpad.net/neutron/
Source0:        http://launchpad.net/neutron/%{release_name}/%{version}/+download/%{servicename}-%{upstream_version}.tar.gz
Source1:        neutron-vpn-agent.service

Obsoletes:      openstack-neutron-vpn-agent < %{version}
Provides:       openstack-neutron-vpn-agent = %{version}-%{release}

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-pbr
BuildRequires:  python-setuptools
BuildRequires:  systemd-units

Requires:       python-%{servicename} = %{version}-%{release}
Requires:       openstack-neutron >= %{version}

%description
This is a %{type} service plugin for Openstack Neutron (Networking) service.


%package -n python-%{servicename}
Summary:        Neutron %{type} Python libraries
Group:          Applications/System

Requires:       python-neutron >= %{version}
Requires:       python-alembic
Requires:       python-jinja2
Requires:       python-netaddr >= 0.7.12
Requires:       python-oslo-config >= 2:1.4.0
Requires:       python-oslo-db >= 1.1.0
Requires:       python-oslo-log >= 1.0.0
Requires:       python-oslo-messaging >= 1.4.0.0
Requires:       python-oslo-serialization >= 1.0.0
Requires:       python-oslo-utils >= 1.0.0
Requires:       python-pbr
Requires:       python-requests
Requires:       python-six
Requires:       python-sqlalchemy


%description -n python-%{servicename}
This is a %{type} service plugin for Openstack Neutron (Networking) service.

This package contains the Neutron %{type} Python library.


%package -n python-%{servicename}-tests
Summary:        Neutron %{type} tests
Group:          Applications/System

Requires:       python-%{servicename} = %{version}-%{release}


%description -n python-%{servicename}-tests
This is a %{type} service plugin for Openstack Neutron (Networking) service.

This package contains Neutron %{type} test files.


%prep
%setup -q -n %{servicename}-%{upstream_version}

# Let's handle dependencies ourselves
rm -f requirements.txt


%build
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{__python2} setup.py build


%install
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{__python2} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Move rootwrap files to proper location
install -d -m 755 %{buildroot}%{_datarootdir}/neutron/rootwrap
mv %{buildroot}/usr/etc/neutron/rootwrap.d/*.filters %{buildroot}%{_datarootdir}/neutron/rootwrap

# Move config files to proper location
install -d -m 755 %{buildroot}%{_sysconfdir}/neutron
mv %{buildroot}/usr/etc/neutron/*.ini %{buildroot}%{_sysconfdir}/neutron
mv %{buildroot}/usr/etc/neutron/*.conf %{buildroot}%{_sysconfdir}/neutron

# Install systemd units
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/neutron-vpn-agent.service

# Create and populate distribution configuration directory for VPN agent
# (the same as for L3 agent)
mkdir -p %{buildroot}%{_datadir}/neutron/l3_agent
ln -s %{_sysconfdir}/neutron/vpn_agent.ini %{buildroot}%{_datadir}/neutron/l3_agent/vpn_agent.conf

# Create configuration directory that can be populated by users with custom *.conf files
mkdir -p %{buildroot}/%{_sysconfdir}/neutron/conf.d/neutron-vpn-agent

# Make sure neutron-server loads new configuration file
mkdir -p %{buildroot}/%{_datadir}/neutron/server
ln -s %{_sysconfdir}/neutron/%{modulename}.conf %{buildroot}%{_datadir}/neutron/server/%{modulename}.conf


%post
%systemd_post neutron-vpn-agent.service


%preun
%systemd_preun neutron-vpn-agent.service


%postun
%systemd_postun_with_restart neutron-vpn-agent.service


%files
%license LICENSE
%doc AUTHORS CONTRIBUTING.rst README.rst
%{_bindir}/neutron-vpn-agent
%{_bindir}/neutron-vpn-netns-wrapper
%{_unitdir}/neutron-vpn-agent.service
%{_datarootdir}/neutron/rootwrap/vpnaas.filters
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/vpn_agent.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/neutron_vpnaas.conf
%dir %{_sysconfdir}/neutron/conf.d
%dir %{_sysconfdir}/neutron/conf.d/neutron-vpn-agent
%{_datadir}/neutron/l3_agent/*.conf
%{_datadir}/neutron/server/%{modulename}.conf


%files -n python-%{servicename}
%{python2_sitelib}/%{modulename}
%{python2_sitelib}/%{modulename}-%{version}-py%{python2_version}.egg-info
%exclude %{python2_sitelib}/%{modulename}/tests


%files -n python-%{servicename}-tests
%{python2_sitelib}/%{modulename}/tests


%changelog
* Wed Jun 22 2016 Alan Pevec <alan.pevec@redhat.com> 2015.1.3-1
- Update to 2015.1.3
