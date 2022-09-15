%{!?sources_gpg: %{!?dlrn:%global sources_gpg 1} }
%global sources_gpg_sign 0x2426b928085a020d8a90d0d879ab7008d0896c8a
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global modulename neutron_vpnaas
%global servicename neutron-vpnaas
%global type VPNaaS
%global common_desc This is a %{type} service plugin for Openstack Neutron (Networking) service.

Name:           openstack-%{servicename}
Version:        XXX
Release:        XXX%{?dist}
Epoch:          1
Summary:        Openstack Networking %{type} plugin

License:        ASL 2.0
URL:            http://launchpad.net/neutron/
Source0:        https://tarballs.openstack.org/%{servicename}/%{servicename}-%{upstream_version}.tar.gz
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
Source101:        https://tarballs.openstack.org/%{servicename}/%{servicename}-%{upstream_version}.tar.gz.asc
Source102:        https://releases.openstack.org/_static/%{sources_gpg_sign}.txt
%endif

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
BuildRequires:  python3-neutron >= %{epoch}:17.0.0
BuildRequires:  python3-pbr
BuildRequires:  python3-setuptools
BuildRequires:  systemd
BuildRequires:	git-core

Requires:       python3-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       openstack-neutron >= %{epoch}:17.0.0

%description
%{common_desc}

%package -n python3-%{servicename}
Summary:        Neutron %{type} Python libraries
%{?python_provide:%python_provide python3-%{servicename}}

Requires:       python3-neutron >= %{epoch}:17.0.0
Requires:       python3-alembic >= 1.6.5
Requires:       python3-jinja2 >= 2.10
Requires:       python3-netaddr >= 0.7.18
Requires:       python3-neutron-lib >= 2.6.0
Requires:       python3-oslo-concurrency >= 3.26.0
Requires:       python3-oslo-config >= 2:8.0.0
Requires:       python3-oslo-db >= 4.44.0
Requires:       python3-oslo-log >= 4.5.0
Requires:       python3-oslo-messaging >= 7.0.0
Requires:       python3-oslo-reports >= 1.18.0
Requires:       python3-oslo-serialization >= 2.25.0
Requires:       python3-oslo-service >= 1.31.0
Requires:       python3-oslo-utils >= 4.5.0
Requires:       python3-pbr >= 4.0.0
Requires:       python3-sqlalchemy >= 1.3.0


%description -n python3-%{servicename}
%{common_desc}

This package contains the Neutron %{type} Python library.


%package -n python3-%{servicename}-tests
Summary:        Neutron %{type} tests
%{?python_provide:%python_provide python3-%{servicename}-tests}

Requires:       python3-neutron-tests
Requires:       python3-%{servicename} = %{epoch}:%{version}-%{release}


%description -n python3-%{servicename}-tests
%{common_desc}

This package contains Neutron %{type} test files.


%prep
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
%{gpgverify}  --keyring=%{SOURCE102} --signature=%{SOURCE101} --data=%{SOURCE0}
%endif
%autosetup -n %{servicename}-%{upstream_version} -S git

# Let's handle dependencies ourselves
%py_req_cleanup

# Kill egg-info in order to generate new SOURCES.txt
rm -rf %{modulename}.egg-info

%build
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{py3_build}

# Generate configuration files
PYTHONPATH=.
for file in `ls etc/oslo-config-generator/*`; do
    oslo-config-generator --config-file=$file
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
%{py3_install}

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


%files -n python3-%{servicename}
%{python3_sitelib}/%{modulename}
%{python3_sitelib}/%{modulename}-%{version}-*.egg-info
%exclude %{python3_sitelib}/%{modulename}/tests


%files -n python3-%{servicename}-tests
%{python3_sitelib}/%{modulename}/tests

%changelog

