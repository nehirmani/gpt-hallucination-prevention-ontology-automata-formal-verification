# PDA (Yığın Otomatı) Sınıfı
# Biçimsel Diller ve Otomatlar dersi - Grup B, Proje 2
# Nobel cümle yapısını yığıt tabanlı parse etmek için kullanılır
#
# Not: JFLAP simülasyonu karakter bazlı ve Bottom-Up (LR) mantığıyla
# çalışmaktadır. Bu Python implementasyonu kelime (token) bazlı ve
# Top-Down (LL) çalışan optimize bir mimariyle tasarlanmıştır.

class PDA:
    def __init__(self):
        # 7-demet: Q, Sigma, Gamma, delta, q0, Z0, F
        self.Q = {'q0', 'q1', 'q2'}
        self.q0 = 'q0'
        self.Z0 = 'Z0'
        self.F = {'q2'}
        self.yigin = []
        self.mevcut_durum = self.q0

    def reset(self):
        self.yigin = [self.Z0]
        self.mevcut_durum = self.q0

    def calistir(self, tokenlar):
        self.reset()
        # q0 -> q1: S'yi yigina it
        self.yigin.append('S')
        self.mevcut_durum = 'q1'

        i = 0 # Token okuma indeksi

        # Yığında Z0 kalana veya okuma hatası olana kadar dön
        while i < len(tokenlar) and len(self.yigin) > 0:
            ust = self.yigin[-1]
            token = tokenlar[i]

            # 1. Terminal Eşleşmesi (Kelime tüketimi)
            if ust == token:
                self.yigin.pop()
                i += 1  # Eşleşme başarılı, sıradaki kelimeye geç

            # 2. Non-terminal Genişletmeleri (Epsilon geçişleri - Kelime tüketilmez!)
            elif ust == 'S':
                self.yigin.pop()
                self.yigin.extend(['VP', 'NP']) # LIFO: NP en üstte olacak

            elif ust == 'NP':
                self.yigin.pop()
                # "the Prize" durumu için basit kontrol
                if token == 'the':
                    self.yigin.extend(['Prize', 'the']) # the en üstte olacak
                else:
                    self.yigin.append(token)

            elif ust == 'VP':
                self.yigin.pop()
                self.yigin.extend(['NP', 'won']) # LIFO: won en üstte olacak

            else:
                return False

        # Yığın sadece Z0 içeriyorsa ve tüm kelimeler okunduysa (Kabul Durumu)
        if len(self.yigin) == 1 and self.yigin[0] == 'Z0' and i == len(tokenlar):
            self.mevcut_durum = 'q2'
            return True

        return False


if __name__ == "__main__":
    pda = PDA()
    print("PDA Test Sonuclari:")
    print("['Einstein', 'won', 'the', 'Prize'] ->", pda.calistir(['Einstein', 'won', 'the', 'Prize']))
    print("['won', 'Einstein']                 ->", pda.calistir(['won', 'Einstein']))
