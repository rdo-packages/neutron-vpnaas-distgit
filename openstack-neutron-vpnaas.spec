# Macros for py2/py3 compatibility
%if 0%{?fedora} || 0%{?rhel} > 7
%global pyver %{python3_pkgversion}
%else
%global pyver 2
%endif
%global pyver_bin python%{pyver}
%global pyver_sitelib %{expand:%{python%{pyver}_sitelib}}
%global pyver_install %{expand:%{py%{pyver}_install}}
%global pyver_build %{expand:%{py%{pyver}_build}}
%global pyver_entrypoint %py%{pyver}_entrypoint %{modulename} %{servicename}
# End of macros for py2/py3 compatibility
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global modulename neutron_vpnaas
%global servicename neutron-vpnaas
%global type VPNaaS
%global common_desc This is a %{type} service plugin for Openstack Neutron (Networking) service.

Name:           openstack-%{servicename}
Version:        15.0.0
Release:        1%{?dist}
Epoch:          1
Summary:        Openstack Networking %{type} plugin

License:        ASL 2.0
URL:            http://launchpad.net/neutron/
Source0:        https://tarballs.openstack.org/%{servicename}/%{servicename}-%{upstream_version}.tar.gz

Obsoletes:      openstack-neutron-vpn-agent < %{version}
Provides:       openstack-neutron-vpn-agent = %{epoch}:%{version}-%{release}

BuildArch:      noarch
BuildRequires:  gawk
BuildRequires:  openstack-macros
BuildRequires:  python%{pyver}-devel
BuildRequires:  python%{pyver}-neutron >= %{epoch}:15.0.0
BuildRequires:  python%{pyver}-pbr
BuildRequires:  python%{pyver}-setuptools
BuildRequires:  systemd
BuildRequires:	git

Requires:       python%{pyver}-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       openstack-neutron >= %{epoch}:15.0.0

%description
%{common_desc}

%package -n python%{pyver}-%{servicename}
Summary:        Neutron %{type} Python libraries
%{?python_provide:%python_provide python%{pyver}-%{servicename}}

Requires:       python%{pyver}-neutron >= %{epoch}:15.0.0
Requires:       python%{pyver}-alembic >= 0.8.10
Requires:       python%{pyver}-jinja2
Requires:       python%{pyver}-netaddr >= 0.7.18
Requires:       python%{pyver}-neutron-lib >= 1.18.0
Requires:       python%{pyver}-oslo-concurrency >= 3.26.0
Requires:       python%{pyver}-oslo-config >= 2:5.2.0
Requires:       python%{pyver}-oslo-db >= 4.27.0
Requires:       python%{pyver}-oslo-log >= 3.36.0
Requires:       python%{pyver}-oslo-messaging >= 5.29.0
Requires:       python%{pyver}-oslo-reports >= 1.18.0
Requires:       python%{pyver}-oslo-serialization >= 2.18.0
Requires:       python%{pyver}-oslo-service >= 1.24.0
Requires:       python%{pyver}-oslo-utils >= 3.33.0
Requires:       python%{pyver}-pbr
Requires:       python%{pyver}-requests
Requires:       python%{pyver}-six >= 1.10.0
Requires:       python%{pyver}-sqlalchemy >= 1.2.0


%description -n python%{pyver}-%{servicename}
%{common_desc}

This package contains the Neutron %{type} Python library.


%package -n python%{pyver}-%{servicename}-tests
Summary:        Neutron %{type} tests
%{?python_provide:%python_provide python%{pyver}-%{servicename}-tests}

Requires:       python%{pyver}-neutron-tests
Requires:       python%{pyver}-%{servicename} = %{epoch}:%{version}-%{release}


%description -n python%{pyver}-%{servicename}-tests
%{common_desc}

This package contains Neutron %{type} test files.


%prep
%autosetup -n %{servicename}-%{upstream_version} -S git

# Let's handle dependencies ourselves
%py_req_cleanup

# Kill egg-info in order to generate new SOURCES.txt
rm -rf %{modulename}.egg-info

%build
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{pyver_build}

# Generate configuration files
PYTHONPATH=.
for file in `ls etc/oslo-config-generator/*`; do
    oslo-config-generator-%{pyver} --config-file=$file
done

find etc -name *.sample | while read filename
do
    filedir=$(dirname $filename)
    file=$(basename $filename .sample)
    mv ${filename} ${filedir}/${file}
done


%install
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{pyver_install}

# Create fake egg-info for the tempest plugin
%pyver_entrypoint

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


%files -n python%{pyver}-%{servicename}
%{pyver_sitelib}/%{modulename}
%{pyver_sitelib}/%{modulename}-%{version}-*.egg-info
%exclude %{pyver_sitelib}/%{modulename}/tests


%files -n python%{pyver}-%{servicename}-tests
%{pyver_sitelib}/%{modulename}/tests
%{pyver_sitelib}/%{modulename}_tests.egg-info

%changelog
* Wed Oct 16 2019 RDO <dev@lists.rdoproject.org> 1:15.0.0-1
- Update to 15.0.0

* Mon Sep 30 2019 RDO <dev@lists.rdoproject.org> 1:15.0.0-0.1.0rc1
- Update to 15.0.0.0rc1

