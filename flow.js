const galleryImages=[
  "https://static.wixstatic.com/media/f45a79_d45318e6b2ea48ee978f7bfd38a6cafe~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_d45318e6b2ea48ee978f7bfd38a6cafe~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_4f726c7641dd41bf8b792999f68dff60~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_4f726c7641dd41bf8b792999f68dff60~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_173dab6fcdbd40119374a69998ed1a9b~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_173dab6fcdbd40119374a69998ed1a9b~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_aa60be1ce20742cd8279430bf5c78ea1~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_aa60be1ce20742cd8279430bf5c78ea1~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_63fda859c6eb417fa07c31c34a48ad30~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_63fda859c6eb417fa07c31c34a48ad30~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_39892ad8dc3048148ff8ba430b839367~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_39892ad8dc3048148ff8ba430b839367~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_d70bc49b60054310917a020e0e4e0b7f~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_d70bc49b60054310917a020e0e4e0b7f~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_e53a73e05322423f96ff79e3007e5a36~mv2.png/v1/fill/w_1200,h_760,q_90/f45a79_e53a73e05322423f96ff79e3007e5a36~mv2.png",
  "https://static.wixstatic.com/media/f45a79_015061c8e7ea4f4a9b1fadf224367ff3~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_015061c8e7ea4f4a9b1fadf224367ff3~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_20bf131a9f1a48529e649295c2742e74~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_20bf131a9f1a48529e649295c2742e74~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_547eb78fd5c54725a71b263f3231864b~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_547eb78fd5c54725a71b263f3231864b~mv2.jpg",
  "https://static.wixstatic.com/media/f45a79_64a2fdd651534ae9941ea071359d099b~mv2.jpg/v1/fill/w_1200,h_760,q_90/f45a79_64a2fdd651534ae9941ea071359d099b~mv2.jpg"
];

let gi=0;

function renderGallery(){
  const main=document.getElementById("galleryMain");
  const grid=document.getElementById("thumbGrid");
  const count=document.getElementById("galleryCount");

  if(!main || !grid || !count) return;

  main.src=galleryImages[gi];
  count.textContent=`${gi+1} / ${galleryImages.length}`;
  grid.innerHTML="";

  for(let k=0;k<6;k++){
    const idx=(gi+k)%galleryImages.length;
    const b=document.createElement("button");
    b.className="thumb"+(k===0?" active":"");
    b.type="button";
    b.innerHTML=`<img src="${galleryImages[idx]}" alt="Tému Stay 官方場地照片 ${idx+1}">`;
    b.onclick=()=>{
      gi=idx;
      renderGallery();
    };
    grid.appendChild(b);
  }
}

document.querySelector(".gprev")?.addEventListener("click",()=>{
  gi=(gi-1+galleryImages.length)%galleryImages.length;
  renderGallery();
});

document.querySelector(".gnext")?.addEventListener("click",()=>{
  gi=(gi+1)%galleryImages.length;
  renderGallery();
});

renderGallery();

document.getElementById("registrationForm")?.addEventListener("submit",(e)=>{
  e.preventDefault();
  location.href="chapter5.html";
});
