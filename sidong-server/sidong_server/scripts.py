def artistAutoCreate():
    file_instance = File.objects.get(id=3)
    for user in range(21, 50):
        user = str(user)
        user_instance = User.objects.create_user(
            username=user, password='1234')
        Artist.objects.create(
            user=user_instance,
            artist_name='필명이여' + user,
            real_name='실명' + user,
            phone="01012341234",
            description="작가 설명, 작가 설명, 작가 설명, 작가 설명",
            category=Artist.PAINTER,
            residence=Artist.SEOUL,
            thumbnail=file_instance,
            representative_work=file_instance,
        )


def artAutoCreate():
    theme = Theme.objects.get(id=1)
    style = Style.objects.get(id=7)
    technique = Technique.objects.get(id=3)
    for user in range(1, 30):
        artist = Artist.objects.get(id=user)
        Art.objects.create(
            artist=artist,
            name=artist.artist_name + "의 test 작품",
            description="test 작품 description",
            medium=0,
            theme=theme,
            style=style,
            technique=technique,
            sale_status=1,
            is_framed=False,
            price=100000,
            orientation=1,
            size="medium",
            width=130,
            height=110,
            images=[20, 21],
        )


def send_email_test():
    from django.core.mail import send_mail
    send_mail(
        'subject',
        'message',
        'jakupteo@gmail.com',
        ['jakupteo@gmail.com'],
    )
