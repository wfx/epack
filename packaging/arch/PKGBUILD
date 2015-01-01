_pkgname=python-epack-git
pkgname=${_pkgname}
pkgver=66.d33590d
pkgrel=1
pkgdesc="epack is a tiny file extractor"
arch=('i686' 'x86_64')
url="https://github.com/wfx/epack"
license=('GPL')
depends=('pv' 'libarchive')
makedepends=('git' 'python' 'python-efl-git')

_gitroot=git://github.com/wfx/epack
_gitname=epack

source=("$_gitroot")
md5sums=('SKIP')

pkgver() {
    cd $_gitname
    echo "$(git rev-list --count HEAD).$(git rev-parse --short HEAD)"
}
package() {
    cd $_gitname
    python setup.py install --root "$pkgdir"
    #install -Dm644 README "$pkgdir"/usr/share/python-epack/README
    #install -Dm644 README "$pkgdir"/usr/share/licenses/python-epack/LICENSE
    find "$pkgdir" -type d -name '.git' -exec rm -r '{}' +
}