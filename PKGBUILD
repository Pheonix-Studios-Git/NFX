pkgname=nfx-bin
pkgver=1.0.0
pkgrel=1
pkgdesc="Cross-platform package manager for the Pheonix Studios ecosystem"

arch=('x86_64')

url="https://github.com/Pheonix-Studios-Git/NFX"

license=('MIT')

depends=('glibc')

provides=('nfx')
conflicts=('nfx')

options=('!strip')

source=(
    "https://github.com/Pheonix-Studios-Git/NFX/releases/download/v${pkgver}/nfx-${pkgver}-linux-x86_64.zip"
)

sha256sums=('359f5a1f0c461b6356addc45767dce09e4b9d8226a25ca8a6b15506783d05e6f')

prepare() {
    cd "$srcdir"
    bsdtar -xf NFX.zip
}

check() {
    "$srcdir/bin/linux/x86_64/dist/nfx" version >/dev/null
}

package() {
    install -Dm755 \
        "$srcdir/bin/linux/x86_64/dist/nfx" \
        "$pkgdir/usr/bin/nfx"

    install -Dm644 \
        "$srcdir/LICENSE" \
        "$pkgdir/usr/share/licenses/$pkgname/LICENSE"

    install -Dm644 \
        "$srcdir/README.md" \
        "$pkgdir/usr/share/doc/$pkgname/README.md"
}