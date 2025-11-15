import logging
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Update
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from .config import settings
from .user import users_json_util


bot = Bot(
    token=settings.bot.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    user = msg.from_user

    users_json_util.set_user(
        tg_id=str(user.id),
        firstname=user.first_name,
        username=user.username,
    )

    await state.clear()

    profile_link = f"tg://user?id={user.id}"

    await msg.reply(
        text=(
            f"Salom <a href='{profile_link}'>{user.first_name or '.'}</a>\n"
            "Men sizga videofayl muqovasini o‘zgartirishga yordam beraman.\n"
            "Menga rasm yoki video yuboring."
        )
    )


@dp.message(F.photo)
async def handle_photo(msg: Message, state: FSMContext):
    data = await state.get_data()

    photo_id = msg.photo[-1].file_id
    video_id = data.get("video_id")

    if not video_id:
        await state.update_data(photo_id=photo_id)
        await msg.answer("Endi bu rasmni muqova qilmoqchi bo‘lgan video yuboring.")
        return

    await msg.answer_video(
        video=video_id, cover=photo_id, caption="✅ Mana sizning video."
    )

    await state.clear()


@dp.message(F.video)
async def handle_video(msg: Message, state: FSMContext):
    data = await state.get_data()

    video_id = msg.video.file_id
    photo_id = data.get("photo_id")

    if not photo_id:
        await state.update_data(video_id=video_id)
        await msg.answer("Endi bu videoga muqova qilmoqchi bo‘lgan rasm yuboring.")
        return

    await msg.answer_video(
        video=video_id, cover=photo_id, caption="✅ Mana sizning video."
    )

    await state.clear()


# -------------------- FASTAPI + WEBHOOK --------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(settings.app.webhook_url)
    logging.info(f"Webhook set: {settings.app.webhook_url}")

    yield

    await bot.delete_webhook()
    logging.info("Webhook removed")
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.post(settings.app.webhook_path)
async def telegram_webhook(request: Request):
    try:
        update = Update.model_validate(await request.json())
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.exception(f"Error while processing update: {e}")
    return {"ok": True}


@app.get("/")
async def root():
    return RedirectResponse(url="docs/")


if __name__ == "__main__":
    logging.basicConfig(
        filename=settings.logging.log_file if not settings.DEBUG else None,
        format=settings.logging.log_format,
        datefmt=settings.logging.log_date_format,
        style="%",
        level=settings.logging.log_level_value,
    )

    uvicorn.run(
        "src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.DEBUG,
    )
