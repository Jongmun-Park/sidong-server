
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
