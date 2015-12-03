%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}


Name:           pdc-client
Version:        0.2.0
Release:        1%{?dist}
Summary:        Console client for interacting with Product Definition Center
Group:          Development/Libraries
License:        MIT
URL:            https://github.com/product-definition-center/pdc-client
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python
Requires:       python-requests
Requires:       python-requests-kerberos
Requires:       beanbag


%description
This package contains a console client for interacting with Product Definition
Center (PDC)


%prep
%setup -q -n %{name}-%{version}


%install
rm -rf %{buildroot}

mkdir -p %{buildroot}/%{python_sitelib}/pdc_client
cp -R pdc_client/* %{buildroot}/%{python_sitelib}/pdc_client

mkdir -p %{buildroot}%{_defaultdocdir}/pdc_client

# Install PDC client command line interface
install -m 0644 -D -p bin/pdc_client %{buildroot}%{_bindir}/pdc_client
install -m 0644 -D -p bin/pdc %{buildroot}%{_bindir}/pdc

install -m 0644 -D -p docs/pdc_client.1 %{buildroot}%{_mandir}/man1/pdc_client.1
gzip %{buildroot}%{_mandir}/man1/pdc_client.1


%files
%{python_sitelib}/pdc_client
%attr(755, root, root) %{_bindir}/pdc_client
%attr(755, root, root) %{_bindir}/pdc
%{_mandir}/man1/pdc_client.1.gz


%changelog
* Thu Dec 03 2015 Xiangyang Chu <xchu@redhat.com> 0.2.0-1
- Add python 2.6 check. (xchu@redhat.com)
- Fix spec URL (rbean@redhat.com)
- Allow PDCClient to be configured with arguments. (rbean@redhat.com)
- Imporve on new `pdc` client.

* Fri Sep 11 2015 Xiangyang Chu <xychu2008@gmail.com> 0.1.0-1
- new package built with tito

