%global jabref_tag v6.0-alpha.6
%global jabref_archive_version 6.0-alpha.6
%global abbreviations_tag 2025-01-07
%global csl_styles_tag v0.2.208
%global csl_locales_tag v0.0.101
# These repositories have no tags, so use the revisions pinned by the parent repository.
%global themes_commit 5d7f4344c7c5c81195ed3574b641fb06e182ab4e
%global ltwa_commit 880536620bc5c42f48647fb66c87fec181e107d3
%global debug_package %{nil}

Name:           jabref
Version:        6.0~alpha.6
Release:        1%{?dist}
Summary:        Bibliography reference manager
License:        MIT
URL:            https://www.jabref.org/
Source0:        https://github.com/JabRef/jabref/archive/refs/tags/%{jabref_tag}.tar.gz
Source1:        https://github.com/JabRef/themes.jabref.org/archive/%{themes_commit}.tar.gz
Source2:        https://github.com/JabRef/abbrv.jabref.org/archive/refs/tags/%{abbreviations_tag}.tar.gz
Source3:        https://github.com/citation-style-language/styles/archive/refs/tags/%{csl_styles_tag}.tar.gz
Source4:        https://github.com/citation-style-language/locales/archive/refs/tags/%{csl_locales_tag}.tar.gz
Source5:        https://github.com/JabRef/ltwa/archive/%{ltwa_commit}.tar.gz

BuildRequires:  java-25-openjdk-devel
BuildRequires:  desktop-file-utils
BuildRequires:  coreutils
BuildRequires:  unzip
BuildRequires:  zip
Requires:       java-25-openjdk
Requires:       javapackages-filesystem

%description
JabRef is an open-source bibliography reference manager for BibTeX and BibLaTeX.

%prep
%autosetup -n jabref-%{jabref_archive_version}
mkdir -p jabgui/src/main/themes.jabref.org \
    jablib/src/main/abbrv.jabref.org \
    jablib/src/main/resources/csl-styles \
    jablib/src/main/resources/csl-locales \
    jablib/src/main/resources/ltwa
tar -xzf %{SOURCE1} --strip-components=1 -C jabgui/src/main/themes.jabref.org
tar -xzf %{SOURCE2} --strip-components=1 -C jablib/src/main/abbrv.jabref.org
tar -xzf %{SOURCE3} --strip-components=1 -C jablib/src/main/resources/csl-styles
tar -xzf %{SOURCE4} --strip-components=1 -C jablib/src/main/resources/csl-locales
tar -xzf %{SOURCE5} --strip-components=1 -C jablib/src/main/resources/ltwa

%build
sed -i '/^org.gradle.java.installations.auto-download=/d' gradle.properties
cat >> gradle.properties <<'EOF'
org.gradle.java.installations.auto-detect=false
org.gradle.java.installations.auto-download=false
org.gradle.java.installations.paths=/usr/lib/jvm/java-25-openjdk
EOF

cat > rpm-local-toolchain.init.gradle <<'EOF'
allprojects {
    afterEvaluate { project ->
        def javaExtension = project.extensions.findByType(org.gradle.api.plugins.JavaPluginExtension)
        if (javaExtension != null) {
            javaExtension.toolchain.vendor = null
        }
    }
}
EOF

JAVA_HOME=/usr/lib/jvm/java-25-openjdk \
    ./gradlew --no-daemon --no-configuration-cache \
    --init-script rpm-local-toolchain.init.gradle \
    -PjavaVersion=25 \
    -PprojVersion=%{version} \
    -PprojVersionInfo=%{version} \
    :jabgui:installDist

%install
install -d -m 0755 %{buildroot}%{_libdir}/jabref
cp -a jabgui/build/install/jabgui/. %{buildroot}%{_libdir}/jabref/

for jar_file in %{buildroot}%{_libdir}/jabref/lib/*.jar; do
    if ! unzip -p "$jar_file" META-INF/MANIFEST.MF | grep -q '^Class-Path:'; then
        continue
    fi
    if unzip -Z1 "$jar_file" | grep -Eiq '^META-INF/[^/]+\.(SF|RSA|DSA|EC)$'; then
        echo "Refusing to modify signed JAR $jar_file" >&2
        exit 1
    fi
    temporary_directory=$(mktemp -d "%{buildroot}/.jabref-manifest.XXXXXX")
    install -d -m 0755 "$temporary_directory/META-INF"
    unzip -p "$jar_file" META-INF/MANIFEST.MF | awk '
        /^Class-Path:/ { skipping_class_path = 1; next }
        skipping_class_path && /^ / { next }
        { skipping_class_path = 0; print }
    ' > "$temporary_directory/META-INF/MANIFEST.MF"
    (cd "$temporary_directory" && zip -q "$jar_file" META-INF/MANIFEST.MF)
    rm -rf "$temporary_directory"
done

install -d -m 0755 %{buildroot}%{_bindir}
ln -s ../$(basename %{_libdir})/jabref/bin/jabgui %{buildroot}%{_bindir}/jabref

install -D -m 0644 jabgui/buildres/linux/JabRef.png \
    %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/jabref.png
cat > jabref.desktop <<'EOF'
[Desktop Entry]
Name=JabRef
GenericName=BibTeX Editor
Comment=Open and manage bibliographies
Exec=jabref %U
Icon=jabref
Terminal=false
Type=Application
Categories=Office;
Keywords=bibtex;biblatex;latex;bibliography;
MimeType=text/x-bibtex;
StartupWMClass=org.jabref.gui.JabRefGUI
EOF
desktop-file-install --dir=%{buildroot}%{_datadir}/applications jabref.desktop

install -D -m 0644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/jabref.desktop

%files
%license %{_licensedir}/%{name}/LICENSE
%doc README.md
%{_bindir}/jabref
%{_libdir}/jabref
%{_datadir}/applications/jabref.desktop
%{_datadir}/icons/hicolor/64x64/apps/jabref.png

%changelog
* Sun Sep 13 2026 JabRef contributors <info@jabref.org> - 6.0~alpha.6-1
- Package JabRef for RPM-based Linux distributions
